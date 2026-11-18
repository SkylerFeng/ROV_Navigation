"""Bounded task memory and action evaluation, independent of ROS and LLM vendor."""
import math
from collections import deque
from pathlib import Path
import numpy as np
from semantic_config import read_object,merge_known,number
ROOT=Path(__file__).resolve().parents[1]

def load_agent(path=None):
    c=read_object(ROOT/'config/semantic/agent.json')
    if path:c=merge_known(c,read_object(path),'agent')
    if type(c['evidence_region_search']) is not bool:raise ValueError('evidence_region_search must be boolean')
    number(c['region_coverage_threshold'],'region_coverage_threshold')
    number(c['region_min_gain_area_m2'],'region_min_gain_area_m2')
    if c['region_coverage_threshold']>1:raise ValueError('region_coverage_threshold must be <=1')
    if type(c['enabled']) is not bool:raise ValueError('agent.enabled must be boolean')
    for k in ('landmark_class_lock_frames','memory_limit','max_viewpoint_attempts','max_consecutive_holds','region_max_expansions'):
        number(c[k],k,integer=True)
    for k in ('landmark_memory_s','category_conflict_radius_m','alternative_region_weight','region_weight','repeat_penalty','failure_cooldown_s','loop_window_s','loop_yaw_deg','loop_max_displacement_m','region_search_budget_s','region_expand_step_m','localization_max_spread_m','approach_update_distance_m','approach_update_interval_s'):
        number(c[k],k,allow_zero=k=='region_weight')
    if c['region_name'] is not None and not isinstance(c['region_name'],str):raise ValueError('region_name must be string or null')
    r=c['coarse_region_xyxy']
    if r is not None:
        r=np.asarray(r,float)
        if r.shape!=(4,) or not np.isfinite(r).all() or r[0]>=r[2] or r[1]>=r[3]:raise ValueError('Region requires xmin,ymin,xmax,ymax in world metres')
    for alternative in c['alternative_regions']:
        r=np.asarray(alternative['bounds'],float)
        if r.shape!=(4,) or not np.isfinite(r).all() or r[0]>=r[2] or r[1]>=r[3]:raise ValueError('Invalid alternative region')
    return c

def resolve_region(config,name,path=ROOT/'config/semantic/search_regions.json'):
    regions=read_object(path)
    if name not in regions:raise ValueError('Unknown search region: '+name)
    r=np.asarray(regions[name],float)
    if r.shape!=(4,) or not np.isfinite(r).all() or r[0]>=r[2] or r[1]>=r[3]:
        raise ValueError('Invalid search region bounds')
    if not config['enabled']:raise ValueError('Search region requires enabled Agent')
    return {**config,'region_name':name,'coarse_region_xyxy':r.tolist(),
            'alternative_regions':[{'name':k,'bounds':v} for k,v in regions.items() if k!=name]}

class TaskAgent:
    def __init__(self,cfg):
        self.cfg=cfg;self.history=deque(maxlen=cfg['memory_limit']);self.current=None
        self.viewpoints={};self.samples=deque();self.holds=0;self.phase='SEARCH';self.counter=0
        self.search_elapsed=0.;self.search_clock=None;self.expansion=0;self.search_events=[];self.target_confirmed=False;self.alternative_index=-1
    def search_settings(self,now,objects,target,position=None,grid=None,candidates=None):
        """Budget only unconfirmed search time; hint is never an obstacle mask."""
        if grid is not None and self.cfg.get('evidence_region_search',False):
            return self.evidence_search_settings(now,objects,target,position,grid,candidates)
        confirmed=any(o.get('confirmed') and o.get('visible_now') and
                      o['category']==target['category'] and o['color']==target['color'] for o in objects)
        self.target_confirmed=confirmed
        alternatives=self.cfg.get('alternative_regions',[])
        in_search_region=True
        if position is not None and 0<=self.alternative_index<len(alternatives):
            r=alternatives[self.alternative_index]['bounds'];x,y=position[:2]
            in_search_region=r[0]<=x<=r[2] and r[1]<=y<=r[3]
        count_interval=in_search_region and getattr(self,'previous_in_search_region',True)
        self.previous_in_search_region=in_search_region
        if count_interval and self.search_clock is not None and not confirmed and self.phase in ('SEARCH','REGION_SEARCH','EXPANDED_SEARCH','ALTERNATIVE_SEARCH','GLOBAL_SEARCH'):
            self.search_elapsed+=max(0,now-self.search_clock)
        self.search_clock=now
        region=self.cfg['coarse_region_xyxy']
        if region is not None and self.search_elapsed>=self.cfg['region_search_budget_s']:
            self.expand_search(now,'search_budget_exhausted')
        if region is not None and self.expansion<=self.cfg['region_max_expansions']:
            pad=self.expansion*self.cfg['region_expand_step_m']
            region=[region[0]-pad,region[1]-pad,region[2]+pad,region[3]+pad]
        else:
            alternatives=self.cfg.get('alternative_regions',[])
            if alternatives and self.alternative_index<0:
                self.alternative_index=0;self.search_elapsed=0.
                self.search_events.append({'time_s':now,'reason':'prior_exhausted_try_alternative','region':alternatives[0]['name']})
            elif 0<=self.alternative_index<len(alternatives) and self.search_elapsed>=self.cfg['region_search_budget_s']:
                self.alternative_index+=1;self.search_elapsed=0.
                self.search_events.append({'time_s':now,'reason':'alternative_budget_exhausted','alternative_index':self.alternative_index})
            region=alternatives[self.alternative_index]['bounds'] if 0<=self.alternative_index<len(alternatives) else None
        self.effective_region=region
        return {'coarse_region_xyxy':region,'region_transfer':region is not None and self.alternative_index>=0,'region_weight':self.cfg['alternative_region_weight'] if region is not None and self.alternative_index>=0 else self.cfg['region_weight']}
    def evidence_search_settings(self,now,objects,target,position,grid,candidates=None):
        """Local observations, not travel/API waiting time, justify releasing a hint."""
        regions=([{'name':self.cfg['region_name'],'bounds':self.cfg['coarse_region_xyxy']}]
                 if self.cfg['coarse_region_xyxy'] is not None else [])+self.cfg.get('alternative_regions',[])
        index=getattr(self,'region_index',0)
        region=regions[index]['bounds'] if index<len(regions) else None
        self.target_confirmed=any(o.get('confirmed') and o.get('visible_now') and
            o['category']==target['category'] and o['color']==target['color'] for o in objects)
        if region is not None:
            cells=np.indices(grid.shape).reshape(2,-1).T
            points=grid.origin+(cells+.5)*grid.res
            mask=(((points>=region[:2])&(points<=region[2:])).all(1)).reshape(grid.shape)&grid.inside&~grid.occupied
            coverage=float((grid.inspected&mask).sum()/max(1,mask.sum())) if grid.inspected is not None else 0.
            scans=[p for p in grid.scan_positions[getattr(self,'region_scan_start',0):]
                   if np.all(np.asarray(p)>=np.asarray(region[:2])-.5) and np.all(np.asarray(p)<=np.asarray(region[2:])+.5)]
            remaining=int((mask&~grid.inspected).sum()) if grid.inspected is not None else int(mask.sum())
            productive=None if candidates is None else [c for c in candidates if c['kind']=='explore' and
                c.get('information_gain_score',0)*grid.res**2>=self.cfg['region_min_gain_area_m2']]
            self.region_evidence={'coverage':coverage,'local_scans':len(scans),'region':regions[index]['name'],
                'uninspected_cells':remaining,'productive_viewpoints':None if productive is None else len(productive)}
            # Never abandon an occluded region merely because the robot spent time
            # aligning or moving there. At least two spatially distinct views and
            # substantial close-range coverage are required.
            distinct=[]
            for p in scans:
                if all(np.linalg.norm(p-q)>.7 for q in distinct):distinct.append(p)
            # Coverage is only a prerequisite. Assess the actual reachable,
            # novelty- and failure-filtered views before giving up a region.
            exhausted=remaining==0 or (productive is not None and not productive)
            if not self.target_confirmed and len(distinct)>=2 and coverage>=self.cfg['region_coverage_threshold'] and exhausted:
                index+=1;self.region_index=index;self.alternative_index=index-1
                self.region_scan_start=len(grid.scan_positions)
                self.search_events.append({'time_s':now,'reason':'regional_viewpoints_exhausted','evidence':dict(self.region_evidence)})
                region=regions[index]['bounds'] if index<len(regions) else None
        self.effective_region=region
        return {'coarse_region_xyxy':region,'region_transfer':region is not None,
                'region_weight':self.cfg['alternative_region_weight'],'regional_information':region is not None}
    def expand_search(self,now,reason):
        if self.cfg['coarse_region_xyxy'] is None or self.expansion>self.cfg['region_max_expansions']:return False
        self.expansion+=1;self.search_elapsed=0.
        self.search_events.append({'time_s':now,'reason':reason,'expansion':self.expansion,
                                   'global_search':self.expansion>self.cfg['region_max_expansions']})
        return True
    def search_phase(self):
        if self.cfg.get('evidence_region_search') and hasattr(self,'region_index'):
            if self.region_index>=1+len(self.cfg.get('alternative_regions',[])):return 'GLOBAL_SEARCH'
            if self.region_index>0:return 'ALTERNATIVE_SEARCH'
        if 0<=self.alternative_index<len(self.cfg.get('alternative_regions',[])):return 'ALTERNATIVE_SEARCH'
        if self.cfg['coarse_region_xyxy'] is None or self.expansion>self.cfg['region_max_expansions']:return 'GLOBAL_SEARCH'
        return 'EXPANDED_SEARCH' if self.expansion else 'REGION_SEARCH'
    def start(self,action,obs,now):
        if self.current:self.complete('ABORTED','superseded',now)
        self.counter+=1
        candidate=next((c for c in obs['candidates'] if c['id']==action.get('candidate_id')),None)
        self.current={'tool_id':self.counter,'action':action['action'],'candidate_id':action.get('candidate_id'),
                      'object_id':action.get('object_id'),'started_s':now,'observation_id':obs['observation_id'],
                      'position':candidate['position'] if candidate else None}
        if action['action']=='explore':
            item=self.viewpoints.setdefault(action['candidate_id'],{'attempts':0,'failures':0,'visited':False,'last_failure_s':None})
            item['attempts']+=1
        self.holds=self.holds+1 if action['action']=='hold' else 0
        self.samples.clear()
        return dict(self.current)
    def complete(self,status,reason,now):
        if self.current is None:return None
        result={**self.current,'status':status,'reason':reason,'ended_s':now,'duration_s':max(0,now-self.current['started_s'])}
        if self.current['action']=='explore':
            item=self.viewpoints[self.current['candidate_id']]
            if status=='SUCCEEDED':item['visited']=True
            elif status in ('FAILED','TIMEOUT'):
                item['failures']+=1;item['last_failure_s']=now
        self.history.append(result);self.current=None;self.samples.clear()
        return result
    def constrain(self,candidates,now):
        result=[]
        for candidate in candidates:
            c=dict(candidate)
            if c['kind']=='explore':
                v=self.viewpoints.get(c['id'],{})
                if v.get('attempts',0)>=self.cfg['max_viewpoint_attempts']:continue
                fail=v.get('last_failure_s')
                if fail is not None and now-fail<self.cfg['failure_cooldown_s']:continue
                c['previous_attempts']=v.get('attempts',0);c['previous_failures']=v.get('failures',0)
                c['score']/=1+self.cfg['repeat_penalty']*c['previous_attempts']
            result.append(c)
        return result
    def validate(self,action,now):
        if action['action']=='hold' and self.holds>=self.cfg['max_consecutive_holds']:raise ValueError('Agent hold budget exhausted; select productive action')
        cid=action.get('candidate_id');v=self.viewpoints.get(cid,{})
        if action['action']=='explore' and (v.get('attempts',0)>=self.cfg['max_viewpoint_attempts'] or
            (v.get('last_failure_s') is not None and now-v['last_failure_s']<self.cfg['failure_cooldown_s'])):
            raise ValueError('Agent rejects repeated or cooling-down viewpoint')
    def update_phase(self,mode,objects,target):
        candidate=any(o['category']==target['category'] and o['color']==target['color'] and o.get('visible_now') for o in objects)
        self.phase={'SUCCEEDED':'DONE','FAILED':'FAILED','RECOVERING':'RECOVERY','APPROACHING':'APPROACH',
                    'VERIFYING':'VERIFY'}.get(mode,'VERIFY' if candidate else self.search_phase())
    def summary(self):
        # Coordinates and images need not enter the language-model prompt.
        return {'phase':self.phase,'coarse_region_xyxy':self.cfg['coarse_region_xyxy'],
                'region_name':self.cfg['region_name'],'effective_region_xyxy':getattr(self,'effective_region',self.cfg['coarse_region_xyxy']),
                'alternative_region_index':self.alternative_index,'search_elapsed_s':self.search_elapsed,'search_expansion':self.expansion,'search_events':list(self.search_events),
                'visited_viewpoints':[k for k,v in self.viewpoints.items() if v['visited']],
                'viewpoint_attempts':{k:dict(v) for k,v in self.viewpoints.items()},
                'region_evidence':getattr(self,'region_evidence',None),'recent_results':[{k:v for k,v in r.items() if k!='position'} for r in self.history],
                'consecutive_holds':self.holds,'max_consecutive_holds':self.cfg['max_consecutive_holds']}
    def loop(self,now,position,yaw,mode):
        if mode not in ('EXPLORING','APPROACHING'):
            self.samples.clear();return None
        if self.samples and now<=self.samples[-1][0]:self.samples.clear()
        self.samples.append((now,list(position[:2]),yaw))
        while len(self.samples)>1 and now-self.samples[1][0]>=self.cfg['loop_window_s']:self.samples.popleft()
        if now-self.samples[0][0]<self.cfg['loop_window_s']:return None
        pts=np.array([x[1] for x in self.samples]);angles=[x[2] for x in self.samples]
        span=float(np.linalg.norm(pts-pts[0],axis=1).max())
        turn=sum(abs(math.atan2(math.sin(b-a),math.cos(b-a))) for a,b in zip(angles,angles[1:]))
        if span<self.cfg['loop_max_displacement_m'] and math.degrees(turn)>self.cfg['loop_yaw_deg']:
            return {'window_s':now-self.samples[0][0],'max_displacement_m':span,'absolute_yaw_deg':math.degrees(turn)}
        return None
