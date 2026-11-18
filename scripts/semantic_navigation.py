"""RGB+range semantic navigation. No simulator object poses or USD access.
Exact timestamp pairing, CPU YOLO, observed-space candidates, A*/EGO goals,
exclusive tracker lease, asynchronous JSON policy with safe error hold.
"""
import argparse,json,math,time,uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Image,CameraInfo
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from experiment import ROOT,load_experiment
from semantic_core import ObjectMemory,ExplorationGrid,localize_detection,rule_action,validate_action,refresh_selected_explore
from semantic_recovery import matching_target,bearing,recovery_heading,scan_entry
from semantic_detector import Detector
from semantic_color import ColorModel
from semantic_support import evaluate_support

def stamp(msg):return msg.header.stamp.sec+msg.header.stamp.nanosec/1e9

def xyz(p):return [p.x,p.y,p.z]

class SemanticNavigation(Node):
    def __init__(self,args):
        super().__init__('rov_semantic_navigation');self.args=args
        from semantic_config import load_task,load_runtime,load_providers
        self.cfg=load_task(args.task_config)
        self.runtime=load_runtime(args.runtime_config)
        from semantic_vision import VisionFrontend,load_vision
        from semantic_agent import TaskAgent,load_agent
        self.vision=VisionFrontend(load_vision(getattr(args,'vision_config',None)))
        agent_cfg=load_agent(getattr(args,'agent_config',None))
        self.agent=TaskAgent(agent_cfg) if agent_cfg['enabled'] else None
        self.task_id=uuid.uuid4().hex[:12];self.sequence=0;self.frame=None;self.odom=None
        self.buffers={};self.last_sensor=-math.inf;self.last_processed=-math.inf
        self.detector=Detector(args.model,self.cfg['detector_confidence'])
        self.color_model=ColorModel(ROOT/'config/semantic/color_model.npz')
        self.memory=ObjectMemory(self.cfg['confirmation_frames'],agent_cfg['category_conflict_radius_m'],
            memory_seconds=agent_cfg['landmark_memory_s'] if agent_cfg['enabled'] else 60.,
            class_lock_frames=agent_cfg['landmark_class_lock_frames'] if agent_cfg['enabled'] else 0)
        c=load_experiment('platform_semantic')
        self.grid=ExplorationGrid(json.loads((ROOT/c['water_boundary']).read_text()),self.cfg['grid_resolution_m'],self.cfg['clearance_m'],inspection_range=self.runtime['exploration']['inspection_range_m'],obstacle_resolution=c['navigation']['planner']['cloud_resolution_m'])
        from static_collision_prior import load_static_xy,seed_grid
        seed_grid(self.grid,load_static_xy(c))
        if c["navigation"]["planner"]["circular_xy_inflation"]:self.grid.inflation_metric="euclidean"
        self.mode='WAITING';self.scan_completed=False;self.scan_accum=0.;self.previous_yaw=None
        self.next_scan_center=None;self.scan_direction=-1.
        self.anchor=None;self.hold_yaw=0.;self.started=None;self.active=None;self.action_started=0
        self.last_result='startup';self.verified_since=None;self.last_tick=-math.inf;self.last_frame_wall=time.monotonic()
        self.goal=self.create_publisher(PoseStamped,'/move_base_simple/goal',10)
        self.motion=self.create_publisher(String,'/rov/semantic/motion',10)
        self.status=self.create_publisher(String,'/rov/semantic/status',10)
        self.planner_state='';self.planner_ready=False;self.future=None;self.pending_observation=None
        self.executor_pool=ThreadPoolExecutor(max_workers=1);self.policy=None
        if args.policy!='rule':
            from semantic_llm import JSONPolicy
            self.policy=JSONPolicy(args.policy,load_providers(args.providers_config)[args.policy],settings=self.runtime['llm'])
        self.create_subscription(Odometry,'/rov/odom',self.receive_odom,10)
        self.create_subscription(String,'/rov/planner_status',self.receive_planner,10)
        self.last_tracking_log=-100.
        self.last_planner_log=-100.
        self.create_subscription(String,'/rov/tracking_status',self.receive_tracking,10)
        for kind,topic,cls in [('rgb','/rov/rgb',Image),('depth','/rov/depth_range',Image),('info','/rov/camera_info',CameraInfo),('pose','/rov/camera_pose',PoseStamped)]:
            self.create_subscription(cls,topic,lambda msg,k=kind:self.receive(k,msg),3)
        self.create_timer(self.runtime['execution']['tick_s'],self.tick)
        args.output.mkdir(parents=True,exist_ok=True)
        self.log=(args.output/'events.jsonl').open('w');self.frames=0;self.path=[];self.last_snapshot=-100
        self.events=0;self.llm_calls=0;self.llm_errors=0;self.scans_at_viewpoint=0;self.failed_approaches=[];self.failed_explores=[];self.last_verify_log=-100.;self.target_anchor=None;self.target_seen=-math.inf;self.recovery_attempts=0;self.recovery_until=-math.inf;self.cooldown_until=-math.inf
        self.debug_publisher=self.create_publisher(String,'/rov/semantic/debug',1)
        self.debug_decision=None;self.debug_stages=[]
        self.debug_preview_source=None;self.debug_preview_cache=None
        self.debug_camera_source=None;self.debug_camera_cache=None;self.debug_camera_error=None
        self.create_timer(.5,self.publish_debug)
        self.record('start',{'policy':args.policy,'model':str(args.model),'task':self.cfg,'task_id':self.task_id})
    def publish_debug(self):
        # Read-only view: never call observation(), which mutates decision state.
        if self.debug_publisher.get_subscription_count()==0:return
        from semantic_debug import snapshot
        payload=snapshot(self)
        if self.debug_camera_source is not None:
            rgb,t,detections=self.debug_camera_source
            try:
                if self.debug_camera_cache is None or self.debug_camera_cache['sim_time']!=t:
                    from semantic_debug_camera import encode_frame
                    self.debug_camera_cache=encode_frame(rgb,t,detections)
                payload['camera']=self.debug_camera_cache
                self.debug_camera_error=None
            except Exception as exc:
                # Debug imagery must never stop navigation or show stale boxes on a new image.
                self.debug_camera_error=type(exc).__name__
        if self.debug_preview_source is not None:
            preview,t=self.debug_preview_source
            try:
                if self.debug_preview_cache is None or self.debug_preview_cache['sim_time']!=t:
                    from semantic_debug_camera import encode_frame
                    self.debug_preview_cache=encode_frame(preview,t,[])
                payload['camera_preview']=self.debug_preview_cache
            except Exception as exc:payload['preview_error']=type(exc).__name__
        payload['camera_error']=self.debug_camera_error
        self.debug_publisher.publish(String(data=json.dumps(payload,ensure_ascii=False,allow_nan=False)))
    def record(self,kind,data):
        if kind=='decision':self.debug_decision={'sim_time':self.now(),**data}
        if kind in ('decision','navigation_no_progress','verification_failed','inflation_escape_started') and getattr(self,'grid',None) is not None:
            # Retain the actual sensor map at a decision/failure, not just the
            # final map. This is diagnostic evidence, never a ground-truth input.
            directory=self.args.output/'diagnostics';directory.mkdir(exist_ok=True)
            name=f'{self.events:05d}_{kind}.npz'
            np.savez_compressed(directory/name,free=self.grid.free,occupied=self.grid.occupied,
                inspected=self.grid.inspected,origin=self.grid.origin,res=self.grid.res,
                safe=self.grid.safe())
            data={**data,'map_snapshot':'diagnostics/'+name,
                  'planner_feedback':getattr(self,'planner_feedback',{}),
                  'tracking_feedback':getattr(self,'tracking_feedback',{})}
        if kind in ('decision','recovery_started','navigation_no_progress','verification_failed','result'):
            action=data.get('action',{})
            self.debug_stages.append({'t':self.now(),'event':kind,'action':action.get('action',data.get('status','')),
                                      'reason':action.get('reason_code',data.get('reason',''))})
            self.debug_stages=self.debug_stages[-6:]

        self.log.write(json.dumps({'event':kind,'sim_time':self.now(),**data},ensure_ascii=False,allow_nan=False)+chr(10));self.log.flush();self.events+=1
    def now(self):return self.get_clock().now().nanoseconds/1e9
    def receive_odom(self,msg):self.odom=msg
    def receive_planner(self,msg):
        try:
            feedback=json.loads(msg.data);previous=self.planner_state
            self.planner_feedback=feedback;self.planner_state=feedback.get('state','');self.planner_ready=True
            if hasattr(self,'log') and (previous!=self.planner_state or self.now()-self.last_planner_log>=1.):
                self.record('planner',feedback);self.last_planner_log=self.now()
        except ValueError:pass
    def receive_tracking(self,msg):
        if self.now()-self.last_tracking_log<1.:return
        try:data=json.loads(msg.data)
        except ValueError:return
        self.tracking_feedback=data
        # A turn that reduces heading error is progress, but oscillation is not.
        if self.mode in ('APPROACHING','EXPLORING') and self.active and data.get('mode')=='ALIGNING':
            error=abs(data.get('heading_error_deg',180.))
            if error<self.active.get('best_heading_error',180.)-self.runtime['execution'].get('heading_progress_deg',8.):
                self.active['best_heading_error']=error
                self.active['progress_time']=self.now()
        self.record('tracking',data);self.last_tracking_log=self.now()
    def receive(self,kind,msg):
        key=(msg.header.stamp.sec,msg.header.stamp.nanosec)
        bundle=self.buffers.setdefault(key,{});bundle[kind]=msg
        if len(bundle)==4:
            if stamp(msg)>self.last_processed:self.frame=bundle
            del self.buffers[key]
        while len(self.buffers)>8:del self.buffers[next(iter(self.buffers))]
    def perceive(self):
        if self.frame is None:return
        frame=self.frame;self.frame=None;rgb_msg=frame['rgb'];dmsg=frame['depth'];t=stamp(rgb_msg)
        if t<=self.last_processed:return
        if rgb_msg.encoding!='rgb8' or dmsg.encoding!='32FC1' or dmsg.is_bigendian:raise ValueError('unsupported sensor encoding')
        rgb=np.frombuffer(rgb_msg.data,np.uint8).reshape(rgb_msg.height,rgb_msg.step)[:,:rgb_msg.width*3].reshape(rgb_msg.height,rgb_msg.width,3)
        depth=np.frombuffer(dmsg.data,np.float32).reshape(dmsg.height,dmsg.step//4)[:,:dmsg.width]
        if depth.shape!=rgb.shape[:2]:raise ValueError('unaligned RGB/depth')
        cp=xyz(frame['pose'].pose.position);q=frame['pose'].pose.orientation;cq=[q.w,q.x,q.y,q.z];k=np.array(frame['info'].k).reshape(3,3)
        raw_sensor_rgb=rgb.copy()
        raw_rgb,rgb,depth,k,vision_meta=self.vision.process(rgb,depth,k,frame['info'].d,frame['info'].distortion_model)
        self.vision_metadata=vision_meta
        color_rgb=raw_rgb if self.vision.cfg['color_source']=='raw' else rgb
        color_model=self.color_model if self.vision.cfg['color_source']=='raw' else None
        processed_rgb=rgb
        if self.vision.cfg['detector_source']=='raw':rgb=raw_rgb
        found=[];rejected_support=0;boxes=self.detector.predict(rgb);detection_audit=[]
        for d in boxes:
            location=localize_detection(color_rgb,depth,k,cp,cq,d['bbox'],color_model)
            if location is not None:
                support=evaluate_support(d,location,self.runtime['perception'],self.cfg['confirmation_frames'])
                location.update(support)
                if support['support_mode']=='rejected':
                    detection_audit.append({**d,**location,'accepted':False,'rejection':'insufficient_depth_or_foreground_support'})
                    rejected_support+=1;continue
                found.append({**d,**location})
                detection_audit.append({**d,**location,'accepted':True})
            else:detection_audit.append({**d,'accepted':False,'rejection':'color_or_range_localization_failed'})
        from semantic_debug_camera import detection_rows
        self.debug_camera_source=(rgb,t,detection_rows(boxes,found))
        self.debug_preview_source=(processed_rgb,t) if self.vision.cfg['method']!='none' else None
        self.memory.update(found,t);self.grid.update(depth,k,cp,cq,xyz(self.odom.pose.pose.position))
        self.last_sensor=t;self.last_processed=t;self.last_frame_wall=time.monotonic();self.frames+=1
        self.path.append([t,*xyz(self.odom.pose.pose.position)])
        if self.frames==1:self.record('initial_observation',{'detections':found})
        if t-self.last_snapshot>=self.runtime['execution']['snapshot_interval_s']:
            if detection_audit:
                directory=self.args.output/'diagnostics';directory.mkdir(exist_ok=True)
                sensor='diagnostics/sensor_'+str(self.frames).zfill(6)+'.npz'
                np.savez_compressed(self.args.output/sensor,rgb=rgb,depth=depth,k=k,cp=cp,cq=cq,sim_time=t)
            else:sensor=None
            self.record('perception',{'sensor_snapshot':sensor,'vision':vision_meta,'detector_audit':detection_audit,'low_support_detections_rejected':rejected_support,'detections':found,'objects':self.memory.observe(t),'free_cells':int(self.grid.free.sum()),'occupied_cells':int(self.grid.occupied.sum()),'inspected_cells':int(self.grid.inspected.sum())})
            self.last_snapshot=t
            np.savez_compressed(self.args.output/'latest_sensor.npz',rgb=rgb,raw_rgb=raw_sensor_rgb,rectified_raw_rgb=raw_rgb,processed_rgb=processed_rgb,depth=depth,k=k,cp=cp,cq=cq)
            import cv2
            cv2.imwrite(str(self.args.output/'latest_processed.jpg'),cv2.cvtColor(processed_rgb,cv2.COLOR_RGB2BGR))
            canvas=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
            for d in found:
                x0,y0,x1,y1=map(int,d['bbox']);cv2.rectangle(canvas,(x0,y0),(x1,y1),(0,255,0),2)
                cv2.putText(canvas,f"{d['color']} {d['category']} {d['range_m']:.2f}m",(x0,max(15,y0-4)),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,255,0),1)
            cv2.imwrite(str(self.args.output/'latest_detection.jpg'),canvas)
    def observation(self,position):
        self.sequence+=1;objects=self.memory.observe(self.now())
        exploration=dict(self.runtime['exploration'])
        agent=getattr(self,'agent',None)
        if agent:
            for obj in objects:
                obj['localization_stable']=obj.get('position_spread_m',0.)<=agent.cfg['localization_max_spread_m']
                obj['confirmed']=obj['confirmed'] and obj['localization_stable']
            previous=len(agent.search_events)
            exploration.update(agent.search_settings(self.now(),objects,self.cfg,position,self.grid))
        candidates=self.grid.candidates(position,objects,self.cfg['surface_standoff_m'],settings=exploration,max_age=self.cfg['max_observation_age_s'],excluded_approaches=self.failed_approaches,excluded_explores=self.failed_explores)
        targets={o['id'] for o in objects if o.get('confirmed',False) and o['category']==self.cfg['category'] and o['color']==self.cfg['color']}
        candidates=[c for c in candidates if c['kind']=='explore' or c.get('object_id') in targets]
        if agent:candidates=agent.constrain(candidates,self.now())
        if agent:
            # First generate real views in the current region, then evaluate
            # whether any useful reachable view remains. Coverage alone loses
            # targets hidden behind the uninspected side of a baffle.
            settings=agent.search_settings(self.now(),objects,self.cfg,position,self.grid,candidates=candidates)
            if settings!= {k:exploration[k] for k in settings if k in exploration}:
                exploration.update(settings)
                candidates=self.grid.candidates(position,objects,self.cfg['surface_standoff_m'],settings=exploration,max_age=self.cfg['max_observation_age_s'],excluded_approaches=self.failed_approaches,excluded_explores=self.failed_explores)
                candidates=agent.constrain([c for c in candidates if c['kind']=='explore' or c.get('object_id') in targets],self.now())
            if len(agent.search_events)>previous:self.record('agent_search_expanded',agent.search_events[-1])
            agent.update_phase(self.mode,objects,self.cfg)
        if not candidates and self.scan_completed and self.scans_at_viewpoint<self.runtime['scan']['max_sectors_per_viewpoint']:
            self.scan_completed=False  # a 120-degree sector is not complete coverage when frontiers run out
        return {'task_id':self.task_id,'observation_id':self.sequence,'instruction':self.cfg['instruction'],
            'target':{'category':self.cfg['category'],'color':self.cfg['color']},'state':self.mode,
            'scan_completed':self.scan_completed,'objects':objects,'candidates':candidates,'last_action_result':self.last_result,
            'max_observation_age_s':self.cfg['max_observation_age_s'],**({'agent_memory':agent.summary()} if agent else {})}
    def remember_target(self,objects):
        obj=matching_target(objects,self.cfg,self.now(),self.cfg['max_observation_age_s'],
                            self.target_anchor,self.runtime['recovery']['association_radius_m'])
        if obj:
            self.target_anchor=list(obj['surface_world']);self.target_seen=obj['last_seen']
        return obj
    def begin_recovery(self,position,yaw,reason):
        cfg=self.runtime['recovery'];now=self.now()
        if self.target_anchor is None or now-self.target_seen>cfg['target_memory_s'] or now<self.cooldown_until:
            return False
        if self.recovery_attempts>=cfg['max_attempts']:
            self.record('recovery_exhausted',{'reason':reason,'attempts':self.recovery_attempts})
            self.cooldown_until=now+cfg['cooldown_s'];self.target_anchor=None;self.recovery_attempts=0
            return False
        self.recovery_attempts+=1;self.mode='RECOVERING';self.action_started=now
        self.hold(position,bearing(position,self.target_anchor));self.scan_completed=True
        self.record('recovery_started',{'reason':reason,'attempt':self.recovery_attempts,'target_surface':self.target_anchor,'position':position})
        return True
    def hold(self,position,yaw):self.anchor=list(position);self.anchor[2]=self.cfg['depth_m'];self.hold_yaw=yaw
    def lease(self,mode,yaw=None):
        self.motion.publish(String(data=json.dumps({'mode':mode,'position':self.anchor,'yaw':self.hold_yaw if yaw is None else yaw,'stamp':self.now()})))
    def finish(self,status,reason):
        self.mode=status;self.last_result=reason
        if getattr(self,'agent',None):
            self.agent_complete('SUCCEEDED' if status=='SUCCEEDED' else 'FAILED',reason)
            self.agent.update_phase(status,[],self.cfg)
            (self.args.output/'agent_memory.json').write_text(json.dumps(self.agent.summary(),ensure_ascii=False,indent=2))
        result={'status':status,'reason':reason,'policy':self.args.policy,'frames':self.frames,'llm_calls':self.llm_calls,
            'simulation_seconds':self.now()-(self.started or self.now()),'last_objects':self.memory.observe(self.now()),'path':self.path}
        (self.args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));self.record('result',result)
        np.savez_compressed(self.args.output/'map.npz',free=self.grid.free,occupied=self.grid.occupied,inspected=self.grid.inspected,origin=self.grid.origin,res=self.grid.res)
    def execute(self,action,obs,position,yaw):
        validate_action(action,obs)
        if getattr(self,'agent',None):
            self.agent.validate(action,self.now())
            self.record('agent_tool_started',self.agent.start(action,obs,self.now()))
        self.record('decision',{'observation':obs,'action':action});self.action_started=self.now()
        kind=action['action'];self.active=None
        if kind=='scan':
            self.scans_at_viewpoint+=1
            self.mode='SCANNING';self.hold(position,yaw);self.scan_accum=0.;self.previous_yaw=yaw;self.scan_direction=-1.
            if self.next_scan_center is not None:
                self.mode='SCAN_ALIGN'
                entry=self.next_scan_center+math.radians(self.runtime['scan']['sweep_deg'])/2
                if self.runtime['scan']['nearest_endpoint']:
                    entry,self.scan_direction=scan_entry(yaw,self.next_scan_center,self.runtime['scan']['sweep_deg'])
                self.hold(position,entry)
                self.record('scan_entry',{'entry_yaw':entry,'sweep_direction':self.scan_direction,'current_yaw':yaw})
                self.next_scan_center=None
        elif kind in ('approach','explore'):
            c=next(c for c in obs['candidates'] if c['id']==action['candidate_id'])
            if kind=='approach':
                obj=next(o for o in obs['objects'] if o['id']==c['object_id'])
                c={**c,'target_surface_at_issue':list(obj['surface_world'])}
            self.active={**c,'issued_at':self.now(),'progress_time':self.now(),'progress_distance':math.dist(position,c['position'])};self.mode='APPROACHING' if kind=='approach' else 'EXPLORING'
            entry=None
            if self.grid is not None:
                from semantic_alignment import entry_heading
                entry=entry_heading(self.grid,position,c['position'],self.runtime['execution']['entry_align_lookahead_m'])
            error=abs(math.atan2(math.sin(entry-yaw),math.cos(entry-yaw))) if entry is not None else 0.
            if entry is not None and error>math.radians(self.runtime['execution']['entry_align_trigger_deg']):
                self.aligned_navigation_mode=self.mode;self.mode='NAV_ALIGN';self.hold(position,entry)
                self.alignment_best_error=error;self.alignment_progress_time=self.now()
                self.record('navigation_entry_alignment',{'yaw':entry,'heading_error_deg':math.degrees(error),'goal':c['position']})
            else:self.publish_navigation_goal(c['position'])
            if kind=='approach':self.remember_target(obs['objects']);self.next_scan_center=None
            if kind=='explore':
                self.scans_at_viewpoint=0
                cell=self.grid.cell(c['position']);self.grid.visits[cell]=self.grid.visits.get(cell,0)+1
            self.scan_completed=False
        elif kind=='hold':self.mode='HOLD';self.hold(position,yaw)
        else:self.finish('FAILED',action['reason_code'])
    def publish_navigation_goal(self,position):
        msg=PoseStamped();msg.header.frame_id='world';msg.header.stamp=self.get_clock().now().to_msg()
        msg.pose.position.x,msg.pose.position.y,msg.pose.position.z=position;msg.pose.orientation.w=1.
        self.goal.publish(msg)
    def decide(self,position,yaw,observation=None):
        obs=observation if observation is not None else self.observation(position);self.hold(position,yaw)
        obj=self.remember_target(obs['objects'])
        if obj and self.now()>=self.cooldown_until:self.hold_yaw=bearing(position,obj['surface_world'])
        if self.policy:
            if self.llm_calls>=self.runtime['execution']['max_llm_calls']:
                self.finish('FAILED','llm_call_budget_exhausted');return
            self.pending_observation=obs;self.future=self.executor_pool.submit(self.policy.decide,obs)
            self.llm_calls+=1;self.mode='DECIDING';self.record('llm_request',{'observation':obs})
        else:self.execute(rule_action(obs),obs,position,yaw)
    def agent_complete(self,status,reason):
        agent=getattr(self,'agent',None)
        if agent:
            result=agent.complete(status,reason,self.now())
            if result:self.record('agent_tool_result',result)
    def tick(self):
        SemanticNavigation._tick(self)
        agent=getattr(self,'agent',None)
        if not agent:return
        agent.update_phase(self.mode,self.memory.observe(self.now()),self.cfg)
        if self.mode=='READY' and agent.current:
            reason=self.last_result
            status=('TIMEOUT' if 'timeout' in reason or 'bounded_scan' in reason else
                    'FAILED' if any(x in reason for x in ('blocked','no_progress','failed','stale')) else
                    'ABORTED' if reason=='target_observed_while_exploring' else 'SUCCEEDED')
            self.agent_complete(status,reason)
        elif self.mode=='RECOVERING' and agent.current:
            self.agent_complete('FAILED','local_recovery_started')
    def _tick(self):
        now=self.now()
        if not self.odom or not self.planner_ready:return
        p=xyz(self.odom.pose.pose.position);q=self.odom.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        if self.anchor is None:self.hold(p,yaw)
        if now-stamp(self.odom)>.5:
            # Let the tracker watchdog expire instead of trusting an old pose.
            return
        if self.mode in ('SUCCEEDED','FAILED'):
            self.lease('hold');self.status.publish(String(data=json.dumps({'state':self.mode,'reason':self.last_result})));return
        try:self.perceive()
        except Exception as e:self.hold(p,yaw);self.finish('FAILED','perception_error:'+type(e).__name__+':'+str(e));self.lease('hold');return
        if now-self.last_sensor>1. or time.monotonic()-self.last_frame_wall>3:
            self.hold(p,yaw)
            if self.mode in ('APPROACHING','EXPLORING','NAV_ALIGN','INFLATION_ESCAPE'):
                self.mode='READY';self.active=None;self.last_result='sensor_stale_replan'
            self.lease('hold')
            if self.started is not None and now-self.last_sensor>5.:
                self.finish('FAILED','sensor_timeout')
            return
        if self.started is None:self.started=now
        if now-self.started>self.cfg['timeout_sim_s']:self.hold(p,yaw);self.finish('FAILED','task_timeout');self.lease('hold');return
        agent=getattr(self,'agent',None)
        if agent:
            loop=agent.loop(now,p,yaw,self.mode)
            if loop:
                self.record('agent_motion_loop',loop)
                if self.active:
                    (self.failed_explores if self.mode=='EXPLORING' else self.failed_approaches).append(list(self.active['position']))
                self.agent_complete('FAILED','rotation_without_translation')
                self.hold(p,yaw);self.mode='READY';self.active=None;self.scan_completed=True
                self.last_result='rotation_without_translation_choose_another_viewpoint'
                self.lease('hold');return
        if self.mode in ('WAITING','READY'):self.decide(p,yaw)
        elif self.mode=='DECIDING':
            if self.target_anchor is not None and now-self.target_seen<self.runtime['recovery']['target_memory_s'] and now>=self.cooldown_until:
                self.remember_target(self.memory.observe(now))
                self.hold_yaw=bearing(p,self.target_anchor)
            if self.future.done():
                action=None
                try:
                    action,meta=self.future.result();self.record('llm_response',{'action':action,**meta})
                    # Re-evaluate candidate geometry and target freshness before execution.
                    current=self.observation(p);current['observation_id']=self.pending_observation['observation_id']
                    if (action['action']=='explore' and
                        any(c['kind']=='approach' for c in current['candidates']) and
                        not any(c['kind']=='approach' for c in self.pending_observation.get('candidates',[]))):
                        # A newly confirmed target supersedes a search request made before
                        # confirmation. Reuse this fresh snapshot instead of rebuilding the
                        # expensive grid and resetting confirmation across another frame gap.
                        current['observation_id']=self.sequence
                        self.record('decision_superseded_by_target',{'previous_action':action,
                                    'fresh_observation_id':current['observation_id']})
                        self.last_result='target_confirmed_during_api_request'
                        self.decide(p,yaw,current)
                        self.lease('hold')
                        return
                    if refresh_selected_explore(action,self.pending_observation,current,self.grid,p):
                        self.record('explore_candidate_revalidated',{'candidate_id':action['candidate_id']})
                    validate_action(action,current);self.execute(action,current,p,yaw);self.llm_errors=0
                except Exception as e:
                    # Only local validation messages are logged; transport errors may contain URLs.
                    detail=str(e)[:200] if isinstance(e,ValueError) else type(e).__name__
                    self.llm_errors+=1
                    self.record('llm_error',{'type':type(e).__name__,'detail':detail,'consecutive_errors':self.llm_errors,'rejected_action':getattr(e,'action',None)})
                    self.hold(p,yaw)
                    self.last_result='previous_decision_rejected: '+detail
                    if self.llm_errors>=self.runtime['llm']['max_consecutive_errors']:
                        self.finish('FAILED','llm_retry_limit: '+detail)
                    else:
                        self.mode='READY'
                        if action and action.get('action')=='approach':
                            self.begin_recovery(p,yaw,'approach_became_invalid')
                self.future=None
        elif self.mode=='RECOVERING':
            self.hold_yaw=recovery_heading(p,self.target_anchor,now-self.action_started,self.runtime['recovery'])
            obs=self.observation(p);obj=self.remember_target(obs['objects'])
            if obj and any(c['kind']=='approach' and c.get('object_id')==obj['id'] for c in obs['candidates']):
                self.hold(p,bearing(p,obj['surface_world']));self.mode='READY';self.last_result='target_reacquired_locally'
                self.record('recovery_reacquired',{'object_id':obj['id']})
            elif now-self.action_started>=self.runtime['recovery']['timeout_s']:
                self.record('recovery_timeout',{'attempt':self.recovery_attempts})
                self.cooldown_until=now+self.runtime['recovery']['cooldown_s']
                self.target_anchor=None;self.recovery_attempts=0
                self.hold(p,yaw);self.mode='READY';self.scan_completed=True;self.last_result='local_recovery_exhausted_explore'
        elif self.mode=='SCAN_ALIGN':
            objects=self.memory.observe(now)
            found=any(o['confirmed'] and o['color']==self.cfg['color'] and o['category']==self.cfg['category'] and o['visible_now'] for o in objects)
            error=abs(math.atan2(math.sin(self.hold_yaw-yaw),math.cos(self.hold_yaw-yaw)))
            if found:
                self.hold(p,yaw);self.mode='READY';self.scan_completed=True;self.last_result='target_observed'
            elif error<math.radians(10) or now-self.action_started>self.runtime['scan']['timeout_s']:
                self.record('scan_alignment_finished',{'heading_error_deg':math.degrees(error)})
                self.mode='SCANNING';self.scan_accum=0.;self.previous_yaw=yaw;self.action_started=now
        elif self.mode=='SCANNING':
            delta=math.atan2(math.sin(yaw-self.previous_yaw),math.cos(yaw-self.previous_yaw));self.scan_accum+=self.scan_direction*delta;self.previous_yaw=yaw
            objs=self.memory.observe(now)
            found=any(o['confirmed'] and o['color']==self.cfg['color'] and o['category']==self.cfg['category'] and o['visible_now'] for o in objs)
            if found or self.scan_accum>=math.radians(self.runtime['scan']['sweep_deg']):
                self.grid.mark_scanned(p)
                self.scan_completed=True;self.last_result='target_observed' if found else 'scan_completed';self.hold(p,yaw);self.mode='READY'
            elif now-self.action_started>self.runtime['scan']['timeout_s']:self.hold(p,yaw);self.scan_completed=True;self.mode='READY';self.last_result='bounded_scan_finished'
        elif self.mode=='NAV_ALIGN':
            error=abs(math.atan2(math.sin(self.hold_yaw-yaw),math.cos(self.hold_yaw-yaw)))
            if error<getattr(self,'alignment_best_error',math.pi)-math.radians(self.runtime['execution']['alignment_progress_deg']):
                self.alignment_best_error=error;self.alignment_progress_time=now
            if now-getattr(self,'alignment_progress_time',self.action_started)>self.runtime['execution']['alignment_progress_timeout_s']:
                from semantic_escape import inflation_escape
                escape=inflation_escape(self.grid,p,self.runtime['recovery']['escape_hull_radius_m'],self.runtime['recovery']['escape_max_distance_m'])
                self.agent_complete('FAILED','alignment_without_progress')
                if escape:
                    self.record('inflation_escape_started',escape)
                    self.mode='INFLATION_ESCAPE';self.action_started=now;self.escape_goal=escape['position'];self.hold(self.escape_goal,yaw)
                else:
                    self.hold(p,yaw);self.finish('FAILED','alignment_without_progress_no_certified_escape')
                self.lease('hold');return
            if error<math.radians(self.runtime['execution']['entry_align_release_deg']):
                # Revalidate after the bounded turn; new observations may block a route.
                costs,_=self.grid.reachable(p)
                if self.grid.cell(self.active['position']) not in costs:
                    self.agent_complete('FAILED','entry_route_changed')
                    self.hold(p,yaw);self.mode='READY';self.last_result='entry_route_changed';self.scan_completed=True
                else:
                    self.mode=self.aligned_navigation_mode
                    self.active['progress_time']=now
                    self.publish_navigation_goal(self.active['position'])
                    self.record('navigation_entry_aligned',{'heading_error_deg':math.degrees(error)})
            elif now-self.action_started>self.runtime['execution']['entry_align_timeout_s']:
                self.agent_complete('FAILED','entry_alignment_timeout')
                self.hold(p,yaw);self.finish('FAILED','entry_alignment_timeout')
        elif self.mode=='INFLATION_ESCAPE':
            from semantic_escape import escape_segment_clear
            if not escape_segment_clear(self.grid,p,self.escape_goal,self.runtime['recovery'].get('escape_hull_radius_m',.373)):
                self.hold(p,yaw);self.finish('FAILED','inflation_escape_new_obstacle');self.lease('hold');return
            if math.dist(p,self.escape_goal)<.07:
                self.record('inflation_escape_completed',{'position':p})
                self.hold(p,yaw);self.mode='READY';self.last_result='inflation_escape_replan';self.scan_completed=True
            elif now-self.action_started>self.runtime['recovery'].get('escape_timeout_s',12.):
                self.hold(p,yaw);self.finish('FAILED','inflation_escape_timeout')
        elif self.mode in ('APPROACHING','EXPLORING'):
            # EGO rejects an inflated start even when the real hull is clear.
            # Do not repeatedly send different distant goals from that same cell.
            if self.grid is not None and now-self.action_started>3. and self.planner_state in ('GEN_NEW_TRAJ','BLOCKED_GOAL'):
                from semantic_escape import inflation_escape
                escape=inflation_escape(self.grid,p,self.runtime['recovery'].get('escape_hull_radius_m',.373),self.runtime['recovery'].get('escape_max_distance_m',.65))
                if escape:
                    self.agent_complete('ABORTED','inflated_start_recovery')
                    self.record('inflation_escape_started',escape)
                    self.mode='INFLATION_ESCAPE';self.action_started=now
                    self.escape_goal=escape['position'];self.hold(self.escape_goal,yaw)
                    self.lease('hold');return
            distance_to_goal=math.dist(p,self.active['position'])
            if self.active['progress_distance']-distance_to_goal>=self.runtime['execution']['progress_distance_m']:
                self.active['progress_distance']=distance_to_goal;self.active['progress_time']=now
            objects=self.memory.observe(now)
            selected=next((o for o in objects if o['id']==self.active.get('object_id')),None)
            if self.mode=='APPROACHING' and selected and (selected.get('category_conflict') or selected['category']!=self.cfg['category']):
                self.record('approach_category_conflict',{'object_id':selected['id'],'category':selected['category']})
                self.agent_complete('ABORTED','category_conflict_reobserve')
                self.hold(p,yaw);self.mode='READY';self.last_result='category_conflict_reobserve'
                self.scan_completed=False;self.target_anchor=None;self.lease('hold');return
            seen_target=any(o['confirmed'] and o['category']==self.cfg['category'] and o['color']==self.cfg['color'] and o['visible_now'] for o in objects)
            agent=getattr(self,'agent',None)
            if self.mode=='APPROACHING' and agent and 'target_surface_at_issue' in self.active:
                obj=next((o for o in objects if o['id']==self.active['object_id']),None)
                if (obj and obj['confirmed'] and obj['visible_now'] and
                    obj.get('position_spread_m',0.)<=agent.cfg['localization_max_spread_m'] and
                    now-self.active['issued_at']>=agent.cfg['approach_update_interval_s'] and
                    math.dist(obj['surface_world'],self.active['target_surface_at_issue'])>=agent.cfg['approach_update_distance_m']):
                    self.record('target_local_refinement',{'previous':self.active['target_surface_at_issue'],'observed':obj['surface_world']})
                    self.agent_complete('ABORTED','target_position_updated')
                    self.hold(p,yaw);self.mode='READY';self.last_result='target_position_updated';self.scan_completed=True
                    return
            if self.mode=='EXPLORING' and now>=self.cooldown_until and now-self.action_started>=self.runtime['recovery']['explore_commit_s'] and seen_target and any(c['kind']=='approach' and any(o['id']==c.get('object_id') and o['category']==self.cfg['category'] and o['color']==self.cfg['color'] for o in objects) for c in self.observation(p)['candidates']):
                self.hold(p,yaw);self.mode='READY';self.last_result='target_observed_while_exploring';self.scan_completed=True
            elif self.planner_state in ('BLOCKED_GOAL','EMERGENCY_STOP') and now-self.action_started>self.runtime['execution']['blocked_grace_s']:
                if self.mode=='EXPLORING':self.failed_explores.append(list(self.active['position']))
                else:self.failed_approaches.append(list(self.active['position']))
                self.hold(p,yaw);self.last_result='blocked_goal';self.mode='READY';self.scan_completed=True
            elif now-self.active['progress_time']>self.runtime['execution']['progress_timeout_s'] and distance_to_goal>=self.cfg['arrival_tolerance_m']:
                self.record('navigation_no_progress',{'goal':self.active['position'],'position':p,'distance_m':distance_to_goal,'mode':self.mode})
                self.hold(p,yaw);self.last_result='no_progress_choose_another_viewpoint';self.scan_completed=True
                if self.mode=='APPROACHING':
                    self.failed_approaches.append(list(self.active['position']));self.mode='READY'
                    self.begin_recovery(p,yaw,'approach_no_progress')
                else:
                    self.failed_explores.append(list(self.active['position']));self.mode='READY'
            elif now-self.action_started>self.cfg['action_timeout_sim_s']:
                if self.mode=='EXPLORING':self.failed_explores.append(list(self.active['position']))
                else:self.failed_approaches.append(list(self.active['position']))
                self.hold(p,yaw);self.last_result='action_timeout';self.mode='READY';self.scan_completed=True
            elif math.dist(p,self.active['position'])<self.cfg['arrival_tolerance_m']:
                if self.mode=='APPROACHING':
                    self.mode='VERIFYING';self.hold(self.active['position'],self.active['yaw']);self.action_started=now;self.verified_since=None;self.verification_aligned_at=None
                else:
                    self.next_scan_center=self.active.get('inspection_yaw')
                    if self.active.get('transfer_continue'):
                        self.scan_completed=True;self.next_scan_center=None
                    self.hold(p,yaw);self.mode='READY';self.last_result='exploration_waypoint_reached'
        elif self.mode=='VERIFYING':
            obj=self.memory.objects.get(self.active['object_id']);speed=math.sqrt(sum(getattr(self.odom.twist.twist.linear,a)**2 for a in 'xyz'))
            verify=self.runtime['verification']
            visible=obj and now-obj['last_seen']<verify['freshness_s'] and obj['confirmed'] and obj['color']==self.cfg['color'] and obj['category']==self.cfg['category']
            distance=math.dist(p[:2],obj['surface_world'][:2]) if obj else 100.
            if visible:
                self.target_anchor=list(obj['surface_world']);self.target_seen=obj['last_seen']
            if visible:self.hold_yaw=math.atan2(obj['surface_world'][1]-p[1],obj['surface_world'][0]-p[0])
            error=abs(math.atan2(math.sin(self.hold_yaw-yaw),math.cos(self.hold_yaw-yaw)))
            aligned_at=getattr(self,'verification_aligned_at',self.action_started)
            if aligned_at is None and error<math.radians(verify['heading_tolerance_deg']):
                self.verification_aligned_at=now;aligned_at=now
            good=visible and self.cfg['surface_standoff_m']-verify['distance_near_margin_m']<=distance<=self.cfg['surface_standoff_m']+verify['distance_far_margin_m'] and speed<self.cfg['max_speed_at_completion'] and error<math.radians(verify['heading_tolerance_deg'])
            if now-self.last_verify_log>=1.:
                self.record('verification',{'object_id':self.active['object_id'],'visible':bool(visible),
                    'observation_age_s':now-obj['last_seen'] if obj else None,'distance_m':distance,
                    'speed_m_s':speed,'heading_error_deg':math.degrees(error),'verification_phase':'ALIGN_TARGET' if aligned_at is None else 'CHECK_TARGET','good':bool(good),'position':p})
                self.last_verify_log=now
                sensor=self.args.output/'latest_sensor.npz'
                if sensor.exists():
                    import shutil
                    shutil.copyfile(sensor,self.args.output/'verification_sensor.npz')
            self.verified_since=(now if self.verified_since is None else self.verified_since) if good else None
            if self.verified_since is not None and now-self.verified_since>=self.cfg['hold_seconds']:self.finish('SUCCEEDED','visual_identity_range_heading_and_hold_verified')
            elif (aligned_at is not None and now-aligned_at>verify['timeout_s']) or now-self.action_started>self.cfg['action_timeout_sim_s']:
                self.failed_approaches.append(list(self.active['position']))
                self.record('verification_failed',{'position':self.active['position'],'object_id':self.active['object_id'],
                    'visible':bool(visible),'distance_m':distance,'speed_m_s':speed,'heading_error_deg':math.degrees(error)})
                self.hold(p,yaw);self.last_result='verification_failed_reobserve_locally';self.scan_completed=True;self.mode='READY'
                self.begin_recovery(p,yaw,'verification_failed')
        elif self.mode=='HOLD' and now-self.action_started>self.runtime['execution']['hold_s']:self.mode='READY';self.last_result='hold_completed'
        self.lease('navigate' if self.mode in ('APPROACHING','EXPLORING') else 'scan' if self.mode=='SCANNING' else 'hold',yaw+self.scan_direction*self.runtime['scan']['yaw_step_rad'] if self.mode=='SCANNING' else None)
        self.status.publish(String(data=json.dumps({'state':self.mode,'reason':self.last_result,'objects':len(self.memory.objects),'frames':self.frames})))
    def close(self):
        if self.mode not in ('SUCCEEDED','FAILED'):self.finish('FAILED','interrupted')
        self.executor_pool.shutdown(wait=False,cancel_futures=True);self.log.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=ROOT/'logs/semantic_detector_lit/train/weights/best.onnx')
    parser.add_argument('--vision-config',type=Path);parser.add_argument('--agent-config',type=Path)
    parser.add_argument('--task-config',type=Path);parser.add_argument('--runtime-config',type=Path);parser.add_argument('--providers-config',type=Path)
    parser.add_argument('--policy',choices=['rule','qwen','deepseek'],default='rule');parser.add_argument('--output',type=Path,required=True)
    args,ros=parser.parse_known_args();rclpy.init(args=ros);node=SemanticNavigation(args)
    try:rclpy.spin(node)
    except (KeyboardInterrupt,ExternalShutdownException):pass
    finally:
        node.close();node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
if __name__=='__main__':main()
