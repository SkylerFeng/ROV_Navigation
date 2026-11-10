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
from semantic_recovery import matching_target,bearing,recovery_heading
from semantic_detector import Detector
from semantic_color import ColorModel

def stamp(msg):return msg.header.stamp.sec+msg.header.stamp.nanosec/1e9

def xyz(p):return [p.x,p.y,p.z]

class SemanticNavigation(Node):
    def __init__(self,args):
        super().__init__('rov_semantic_navigation');self.args=args
        from semantic_config import load_task,load_runtime,load_providers
        self.cfg=load_task(args.task_config)
        self.runtime=load_runtime(args.runtime_config)
        self.task_id=uuid.uuid4().hex[:12];self.sequence=0;self.frame=None;self.odom=None
        self.buffers={};self.last_sensor=-math.inf;self.last_processed=-math.inf
        self.detector=Detector(args.model,self.cfg['detector_confidence'])
        self.color_model=ColorModel(ROOT/'config/semantic/color_model.npz')
        self.memory=ObjectMemory(self.cfg['confirmation_frames'])
        c=load_experiment('platform_semantic')
        self.grid=ExplorationGrid(json.loads((ROOT/c['water_boundary']).read_text()),self.cfg['grid_resolution_m'],self.cfg['clearance_m'],inspection_range=self.runtime['exploration']['inspection_range_m'])
        self.mode='WAITING';self.scan_completed=False;self.scan_accum=0.;self.previous_yaw=None
        self.next_scan_center=None
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
        self.create_subscription(String,'/rov/tracking_status',self.receive_tracking,10)
        for kind,topic,cls in [('rgb','/rov/rgb',Image),('depth','/rov/depth_range',Image),('info','/rov/camera_info',CameraInfo),('pose','/rov/camera_pose',PoseStamped)]:
            self.create_subscription(cls,topic,lambda msg,k=kind:self.receive(k,msg),3)
        self.create_timer(self.runtime['execution']['tick_s'],self.tick)
        args.output.mkdir(parents=True,exist_ok=True)
        self.log=(args.output/'events.jsonl').open('w');self.frames=0;self.path=[];self.last_snapshot=-100
        self.events=0;self.llm_calls=0;self.llm_errors=0;self.scans_at_viewpoint=0;self.failed_approaches=[];self.failed_explores=[];self.last_verify_log=-100.;self.target_anchor=None;self.target_seen=-math.inf;self.recovery_attempts=0;self.recovery_until=-math.inf;self.cooldown_until=-math.inf
        self.record('start',{'policy':args.policy,'model':str(args.model),'task':self.cfg,'task_id':self.task_id})
    def record(self,kind,data):
        self.log.write(json.dumps({'event':kind,'sim_time':self.now(),**data},ensure_ascii=False,allow_nan=False)+chr(10));self.log.flush();self.events+=1
    def now(self):return self.get_clock().now().nanoseconds/1e9
    def receive_odom(self,msg):self.odom=msg
    def receive_planner(self,msg):
        try:self.planner_state=json.loads(msg.data).get('state','');self.planner_ready=True
        except ValueError:pass
    def receive_tracking(self,msg):
        if self.now()-self.last_tracking_log<1.:return
        try:data=json.loads(msg.data)
        except ValueError:return
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
        found=[];boxes=self.detector.predict(rgb)
        for d in boxes:
            location=localize_detection(rgb,depth,k,cp,cq,d['bbox'],self.color_model)
            if location is not None:found.append({**d,**location})
        self.memory.update(found,t);self.grid.update(depth,k,cp,cq,xyz(self.odom.pose.pose.position))
        self.last_sensor=t;self.last_processed=t;self.last_frame_wall=time.monotonic();self.frames+=1
        self.path.append([t,*xyz(self.odom.pose.pose.position)])
        if self.frames==1:self.record('initial_observation',{'detections':found})
        if t-self.last_snapshot>=self.runtime['execution']['snapshot_interval_s']:
            self.record('perception',{'detections':found,'objects':self.memory.observe(t),'free_cells':int(self.grid.free.sum()),'occupied_cells':int(self.grid.occupied.sum()),'inspected_cells':int(self.grid.inspected.sum())})
            self.last_snapshot=t
            np.savez_compressed(self.args.output/'latest_sensor.npz',rgb=rgb,depth=depth,k=k,cp=cp,cq=cq)
            import cv2
            canvas=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
            for d in found:
                x0,y0,x1,y1=map(int,d['bbox']);cv2.rectangle(canvas,(x0,y0),(x1,y1),(0,255,0),2)
                cv2.putText(canvas,f"{d['color']} {d['category']} {d['range_m']:.2f}m",(x0,max(15,y0-4)),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,255,0),1)
            cv2.imwrite(str(self.args.output/'latest_detection.jpg'),canvas)
    def observation(self,position):
        self.sequence+=1;objects=self.memory.observe(self.now())
        candidates=self.grid.candidates(position,objects,self.cfg['surface_standoff_m'],settings=self.runtime['exploration'],max_age=self.cfg['max_observation_age_s'],excluded_approaches=self.failed_approaches,excluded_explores=self.failed_explores)
        targets={o['id'] for o in objects if o['category']==self.cfg['category'] and o['color']==self.cfg['color']}
        candidates=[c for c in candidates if c['kind']=='explore' or c.get('object_id') in targets]
        if not candidates and self.scan_completed and self.scans_at_viewpoint<self.runtime['scan']['max_sectors_per_viewpoint']:
            self.scan_completed=False  # a 120-degree sector is not complete coverage when frontiers run out
        return {'task_id':self.task_id,'observation_id':self.sequence,'instruction':self.cfg['instruction'],
            'target':{'category':self.cfg['category'],'color':self.cfg['color']},'state':self.mode,
            'scan_completed':self.scan_completed,'objects':objects,'candidates':candidates,'last_action_result':self.last_result,
            'max_observation_age_s':self.cfg['max_observation_age_s']}
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
        result={'status':status,'reason':reason,'policy':self.args.policy,'frames':self.frames,'llm_calls':self.llm_calls,
            'simulation_seconds':self.now()-(self.started or self.now()),'last_objects':self.memory.observe(self.now()),'path':self.path}
        (self.args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));self.record('result',result)
        np.savez_compressed(self.args.output/'map.npz',free=self.grid.free,occupied=self.grid.occupied,inspected=self.grid.inspected,origin=self.grid.origin,res=self.grid.res)
    def execute(self,action,obs,position,yaw):
        validate_action(action,obs);self.record('decision',{'observation':obs,'action':action});self.action_started=self.now()
        kind=action['action'];self.active=None
        if kind=='scan':
            self.scans_at_viewpoint+=1
            self.mode='SCANNING';self.hold(position,yaw);self.scan_accum=0.;self.previous_yaw=yaw
            if self.next_scan_center is not None:
                self.mode='SCAN_ALIGN'
                self.hold(position,self.next_scan_center+math.radians(self.runtime['scan']['sweep_deg'])/2)
                self.next_scan_center=None
        elif kind in ('approach','explore'):
            c=next(c for c in obs['candidates'] if c['id']==action['candidate_id'])
            self.active={**c,'issued_at':self.now(),'progress_time':self.now(),'progress_distance':math.dist(position,c['position'])};self.mode='APPROACHING' if kind=='approach' else 'EXPLORING'
            msg=PoseStamped();msg.header.frame_id='world';msg.header.stamp=self.get_clock().now().to_msg()
            msg.pose.position.x,msg.pose.position.y,msg.pose.position.z=c['position'];msg.pose.orientation.w=1.
            self.goal.publish(msg)
            if kind=='approach':self.remember_target(obs['objects']);self.next_scan_center=None
            if kind=='explore':
                self.scans_at_viewpoint=0
                cell=self.grid.cell(c['position']);self.grid.visits[cell]=self.grid.visits.get(cell,0)+1
            self.scan_completed=False
        elif kind=='hold':self.mode='HOLD';self.hold(position,yaw)
        else:self.finish('FAILED',action['reason_code'])
    def decide(self,position,yaw):
        obs=self.observation(position);self.hold(position,yaw)
        obj=self.remember_target(obs['objects'])
        if obj and self.now()>=self.cooldown_until:self.hold_yaw=bearing(position,obj['surface_world'])
        if self.policy:
            if self.llm_calls>=self.runtime['execution']['max_llm_calls']:
                self.finish('FAILED','llm_call_budget_exhausted');return
            self.pending_observation=obs;self.future=self.executor_pool.submit(self.policy.decide,obs)
            self.llm_calls+=1;self.mode='DECIDING';self.record('llm_request',{'observation':obs})
        else:self.execute(rule_action(obs),obs,position,yaw)
    def tick(self):
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
            if self.mode in ('APPROACHING','EXPLORING'):
                self.mode='READY';self.active=None;self.last_result='sensor_stale_replan'
            self.lease('hold')
            if self.started is not None and now-self.last_sensor>5.:
                self.finish('FAILED','sensor_timeout')
            return
        if self.started is None:self.started=now
        if now-self.started>self.cfg['timeout_sim_s']:self.hold(p,yaw);self.finish('FAILED','task_timeout');self.lease('hold');return
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
            delta=math.atan2(math.sin(yaw-self.previous_yaw),math.cos(yaw-self.previous_yaw));self.scan_accum+=abs(delta);self.previous_yaw=yaw
            objs=self.memory.observe(now)
            found=any(o['confirmed'] and o['color']==self.cfg['color'] and o['category']==self.cfg['category'] and o['visible_now'] for o in objs)
            if found or self.scan_accum>=math.radians(self.runtime['scan']['sweep_deg']):
                self.grid.mark_scanned(p)
                self.scan_completed=True;self.last_result='target_observed' if found else 'scan_completed';self.hold(p,yaw);self.mode='READY'
            elif now-self.action_started>self.runtime['scan']['timeout_s']:self.hold(p,yaw);self.scan_completed=True;self.mode='READY';self.last_result='bounded_scan_finished'
        elif self.mode in ('APPROACHING','EXPLORING'):
            distance_to_goal=math.dist(p,self.active['position'])
            if self.active['progress_distance']-distance_to_goal>=self.runtime['execution']['progress_distance_m']:
                self.active['progress_distance']=distance_to_goal;self.active['progress_time']=now
            objects=self.memory.observe(now)
            seen_target=any(o['confirmed'] and o['category']==self.cfg['category'] and o['color']==self.cfg['color'] and o['visible_now'] for o in objects)
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
                    self.mode='VERIFYING';self.hold(self.active['position'],self.active['yaw']);self.action_started=now;self.verified_since=None
                else:
                    self.next_scan_center=self.active.get('inspection_yaw')
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
            good=visible and self.cfg['surface_standoff_m']-verify['distance_near_margin_m']<=distance<=self.cfg['surface_standoff_m']+verify['distance_far_margin_m'] and speed<self.cfg['max_speed_at_completion'] and error<math.radians(verify['heading_tolerance_deg'])
            if now-self.last_verify_log>=1.:
                self.record('verification',{'object_id':self.active['object_id'],'visible':bool(visible),
                    'observation_age_s':now-obj['last_seen'] if obj else None,'distance_m':distance,
                    'speed_m_s':speed,'heading_error_deg':math.degrees(error),'good':bool(good),'position':p})
                self.last_verify_log=now
                sensor=self.args.output/'latest_sensor.npz'
                if sensor.exists():
                    import shutil
                    shutil.copyfile(sensor,self.args.output/'verification_sensor.npz')
            self.verified_since=(now if self.verified_since is None else self.verified_since) if good else None
            if self.verified_since is not None and now-self.verified_since>=self.cfg['hold_seconds']:self.finish('SUCCEEDED','visual_identity_range_heading_and_hold_verified')
            elif now-self.action_started>verify['timeout_s']:
                self.failed_approaches.append(list(self.active['position']))
                self.record('verification_failed',{'position':self.active['position'],'object_id':self.active['object_id'],
                    'visible':bool(visible),'distance_m':distance,'speed_m_s':speed,'heading_error_deg':math.degrees(error)})
                self.hold(p,yaw);self.last_result='verification_failed_reobserve_locally';self.scan_completed=True;self.mode='READY'
                self.begin_recovery(p,yaw,'verification_failed')
        elif self.mode=='HOLD' and now-self.action_started>self.runtime['execution']['hold_s']:self.mode='READY'
        self.lease('navigate' if self.mode in ('APPROACHING','EXPLORING') else 'scan' if self.mode=='SCANNING' else 'hold',yaw-self.runtime['scan']['yaw_step_rad'] if self.mode=='SCANNING' else None)
        self.status.publish(String(data=json.dumps({'state':self.mode,'reason':self.last_result,'objects':len(self.memory.objects),'frames':self.frames})))
    def close(self):
        if self.mode not in ('SUCCEEDED','FAILED'):self.finish('FAILED','interrupted')
        self.executor_pool.shutdown(wait=False,cancel_futures=True);self.log.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,default=ROOT/'logs/semantic_detector_lit/train/weights/best.onnx')
    parser.add_argument('--task-config',type=Path);parser.add_argument('--runtime-config',type=Path);parser.add_argument('--providers-config',type=Path)
    parser.add_argument('--policy',choices=['rule','qwen','deepseek'],default='rule');parser.add_argument('--output',type=Path,required=True)
    args,ros=parser.parse_known_args();rclpy.init(args=ros);node=SemanticNavigation(args)
    try:rclpy.spin(node)
    except (KeyboardInterrupt,ExternalShutdownException):pass
    finally:
        node.close();node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
if __name__=='__main__':main()
