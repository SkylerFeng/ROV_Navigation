"""Sensor-only semantic geometry, occupied/free/unknown grid and action contract.
No USD, scene object catalogue, or simulator ground-truth semantic access here.
"""
import heapq
import math
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label


def rotation(q):
    q=np.asarray(q,float)
    if q.shape!=(4,) or not np.isfinite(q).all() or np.linalg.norm(q)<1e-8:raise ValueError('invalid quaternion')
    w,x,y,z=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def range_points(depth,k,position,q,stride=1):
    """distance_to_camera is ray range, not optical Z depth."""
    k=np.asarray(k,float).reshape(3,3);d=np.asarray(depth)[::stride,::stride]
    v,u=np.mgrid[:depth.shape[0]:stride,:depth.shape[1]:stride]
    rays=np.stack([(u-k[0,2])/k[0,0],(v-k[1,2])/k[1,1],np.ones_like(u)],axis=-1)
    rays/=np.linalg.norm(rays,axis=-1,keepdims=True)
    valid=np.isfinite(d)&(d>.08)&(d<8.)
    return rays[valid]*d[valid,None]@rotation(q).T+np.asarray(position),valid


def color_mask(rgb):
    import cv2
    hsv=cv2.cvtColor(np.asarray(rgb,np.uint8),cv2.COLOR_RGB2HSV)
    h,s,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
    eligible=(s>65)&(v>35)
    masks={'yellow':eligible&(h>=16)&(h<=43),'blue':eligible&(h>=88)&(h<=138),
           'red':eligible&((h<=12)|(h>=168))}
    counts={k:int(m.sum()) for k,m in masks.items()};best=max(counts,key=counts.get)
    count=counts[best];area=h.size
    if count<max(12,.06*area):return 'unknown',np.zeros(h.shape,bool),0.
    return best,masks[best],count/max(1,sum(counts.values()))


def localize_detection(rgb,depth,k,position,q,box,color_model=None):
    """Color foreground + robust range rejects background within detector bbox.
    Returns a visible surface centroid, NOT an inferred complete object center.
    """
    h,w=depth.shape;x0,y0,x1,y1=np.asarray(box,float)
    if not np.isfinite([x0,y0,x1,y1]).all():return None
    x0,y0=max(0,int(x0)),max(0,int(y0));x1,y1=min(w,int(math.ceil(x1))),min(h,int(math.ceil(y1)))
    if x1-x0<4 or y1-y0<4:return None
    color,mask,score=(color_model.classify if color_model else color_mask)(rgb[y0:y1,x0:x1]);d=depth[y0:y1,x0:x1]
    valid=mask&np.isfinite(d)&(d>.15)&(d<7.5)
    if valid.sum()<15:return None
    med=np.median(d[valid]);valid &= np.abs(d-med)<max(.08,.06*med)
    if valid.sum()<12:return None
    v,u=np.where(valid);u=u+x0;v=v+y0;k=np.asarray(k).reshape(3,3)
    rays=np.column_stack([(u-k[0,2])/k[0,0],(v-k[1,2])/k[1,1],np.ones(len(u))])
    rays/=np.linalg.norm(rays,axis=1,keepdims=True)
    pts=(rays*d[valid,None])@rotation(q).T+position
    surface=np.median(pts,axis=0)
    return {'color':color,'color_score':score,'surface_world':surface.tolist(),
            'range_m':float(med),'depth_samples':int(valid.sum()),
            'depth_mad_m':float(np.median(np.abs(d[valid]-med))),'localization_valid':True}


class ObjectMemory:
    def __init__(self,confirmation_frames=3):self.objects={};self.next_id=1;self.confirmation_frames=confirmation_frames
    def update(self,detections,now):
        matched=set()
        for d in sorted(detections,key=lambda x:x['detector_score'],reverse=True):
            choices=[(math.dist(o['surface_world'],d['surface_world']),key) for key,o in self.objects.items()
                     if key not in matched and o['category']==d['category'] and o['color']==d['color'] and now-o['last_seen']<15]
            dist,key=min(choices,default=(float('inf'),None))
            if dist>.55:
                key=f'obj_{self.next_id:03d}';self.next_id+=1
                self.objects[key]={'id':key,'hits':0,'first_seen':now}
            old=self.objects[key];hits=old['hits']+1 if now-old.get('last_seen',now)<1.5 else 1
            smoothed=(.65*np.asarray(old['surface_world'])+.35*np.asarray(d['surface_world'])).tolist() if 'surface_world' in old else d['surface_world']
            old.update(d);old.update(surface_world=smoothed,hits=hits,last_seen=now,confirmed=hits>=self.confirmation_frames)
            matched.add(key)
        self.objects={k:o for k,o in self.objects.items() if now-o['last_seen']<60}
    def observe(self,now):
        return [{**o,'observation_age_s':max(0,now-o['last_seen']),'visible_now':now-o['last_seen']<1.,'approach_candidate_ids':[]} for o in self.objects.values()]


class ExplorationGrid:
    def __init__(self,boundary,resolution=.15,clearance=.5,inspection_range=None):
        from matplotlib.path import Path
        self.res=float(resolution);self.clearance=float(clearance)
        boundary=np.asarray(boundary);self.origin=np.floor((boundary.min(0)-1)/self.res)*self.res
        shape=np.ceil((boundary.max(0)+1-self.origin)/self.res).astype(int)
        self.shape=tuple(shape);cells=np.indices(self.shape).reshape(2,-1).T
        self.inside=Path(boundary).contains_points(self.origin+(cells+.5)*self.res).reshape(self.shape)
        self.free=np.zeros(self.shape,bool);self.occupied=np.zeros(self.shape,bool);self.visits={};self.scan_positions=[]
        self.inspection_range=inspection_range
        self.inspected=np.zeros(self.shape,bool) if inspection_range is not None else None
        self._safe=None
    def cell(self,xy):return tuple(np.floor((np.asarray(xy)[:2]-self.origin)/self.res).astype(int))
    def xy(self,cell):return self.origin+(np.asarray(cell)+.5)*self.res
    def valid(self,c):return 0<=c[0]<self.shape[0] and 0<=c[1]<self.shape[1]
    def update(self,depth,k,cp,cq,robot):
        # Ray segments inside the navigation slab provide free-space evidence
        # even when their endpoint is the floor/ceiling outside that slab.
        pts,_=range_points(depth,k,cp,cq,stride=8)
        cp=np.asarray(cp);delta=pts-cp
        ranges=np.linalg.norm(delta,axis=1)
        distance=np.arange(.075,8.,self.res*.5)
        scale=distance[None,:]/np.maximum(ranges[:,None],1e-6)
        samples=cp+delta[:,None,:]*scale[:,:,None]
        valid=(distance[None,:]<ranges[:,None]-.2)&(samples[:,:,2]>.84)&(samples[:,:,2]<1.28)
        cells=np.floor((samples[:,:,:2][valid]-self.origin)/self.res).astype(int)
        if len(cells):
            ok=(cells>=0).all(1)&(cells<self.shape).all(1);cells=cells[ok]
            self.free[tuple(cells.T)]=True
        if self.inspected is not None:
            close=valid & (distance[None,:]<=self.inspection_range)
            seen=np.floor((samples[:,:,:2][close]-self.origin)/self.res).astype(int)
            if len(seen):
                seen=seen[(seen>=0).all(1)&(seen<self.shape).all(1)]
                self.inspected[tuple(seen.T)]=True
        # Free-space rays are subsampled for cost, but obstacle endpoints must
        # match the dense planner cloud. Sparse endpoints missed thin geometry
        # and proposed goals that EGO then rejected as occupied.
        dense,_=range_points(depth,k,cp,cq,stride=1)
        ends=dense[(dense[:,2]>.84)&(dense[:,2]<1.28)].copy()
        ends[:,:2]=(np.floor(ends[:,:2]/.1)+.5)*.1  # same occupied XY cells as local_map.py
        cells=np.floor((ends[:,:2]-self.origin)/self.res).astype(int)
        if len(cells):
            ok=(cells>=0).all(1)&(cells<self.shape).all(1);cells=cells[ok]
            self.occupied[tuple(cells.T)]=True
        # Only the currently occupied vehicle footprint is known free without rays.
        c=self.cell(robot);r=int(math.ceil(.32/self.res))
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                p=(c[0]+dx,c[1]+dy)
                if self.valid(p) and math.hypot(dx,dy)*self.res<=.32:self.free[p]=True
        self.free &= self.inside & ~self.occupied;self._safe=None
    def safe(self):
        if self._safe is None:
            # Inflate observed obstacles and walls; require ray-observed center cells.
            clear=distance_transform_edt(~(self.occupied|~self.inside))*self.res
            self._safe=self.free&(clear>self.clearance+self.res*.71)
        return self._safe
    def reachable(self,start):
        root=self.cell(start);safe=self.safe();cost={};parent={}
        if not self.valid(root) or not self.free[root] or self.occupied[root]:return cost,parent
        # Newly observed geometry can put the current pose inside inflation.
        # Permit only monotonic-clearance escape in observed free cells, never
        # a new destination inside inflation or a route cutting through it.
        clearance=distance_transform_edt(~(self.occupied|~self.inside))*self.res
        def allowed(a,b):
            if not self.valid(b) or not self.free[b] or self.occupied[b] or not self.inside[b]:return False
            if safe[b]:return True
            return not safe[a] and clearance[b]>=clearance[a]-1e-9
        cost[root]=0.;queue=[(0.,root)]
        while queue:
            d,c=heapq.heappop(queue)
            if d>cost[c]:continue
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                v=(c[0]+dx,c[1]+dy)
                if not allowed(c,v):continue
                if dx and dy and not(allowed(c,(c[0]+dx,c[1])) and allowed(c,(c[0],c[1]+dy))):continue
                nd=d+math.hypot(dx,dy)*self.res
                if nd<cost.get(v,float('inf')):cost[v]=nd;parent[v]=c;heapq.heappush(queue,(nd,v))
        return {c:d for c,d in cost.items() if safe[c]},parent
    def mark_scanned(self,position):
        self.scan_positions.append(np.asarray(position[:2],float))

    def visible_unknown_gain(self,cell,meaningful,with_heading=False):
        # Count unknown cells reachable by sight without crossing an observed wall.
        visible=set();angles=np.linspace(-np.pi,np.pi,48,endpoint=False);ray_gains=[]
        for angle in angles:
            ray_cells=set()
            direction=np.array([np.cos(angle),np.sin(angle)])
            for distance in np.arange(self.res,(self.inspection_range or 3.)+.01,self.res):
                c=self.cell(self.xy(cell)+direction*distance)
                if not self.valid(c) or not self.inside[c] or self.occupied[c]:break
                if meaningful[c]:visible.add(c);ray_cells.add(c)
                # Uninspected free space also needs a close visual observation.
                # Unknown space is potential information, not an observed wall.
            ray_gains.append(len(ray_cells))
        if with_heading:
            scores=[sum(g for a,g in zip(angles,ray_gains) if abs(math.atan2(math.sin(a-center),math.cos(a-center)))<=math.pi/2) for center in angles]
            preferred=math.atan2(sum(g*math.sin(a) for a,g in zip(angles,ray_gains)),sum(g*math.cos(a) for a,g in zip(angles,ray_gains)))
            best=max(range(len(angles)),key=lambda i:(scores[i],math.cos(angles[i]-preferred)))
            return len(visible),float(angles[best])
        return len(visible)

    def candidates(self,robot,objects,standoff=.8,settings=None,max_age=2.,excluded_approaches=(),excluded_explores=()):
        settings=settings or {}
        cost,parent=self.reachable(robot);candidates=[]
        if not cost:return candidates
        cells=list(cost);xy=np.array([self.xy(c) for c in cells])
        for obj in objects:
            if not obj['confirmed'] or obj['observation_age_s']>max_age:continue
            target=np.array(obj['surface_world'][:2]);distance=np.linalg.norm(xy-target,axis=1)
            eligible=np.flatnonzero((distance>=standoff)&(distance<=standoff+.28))
            if not len(eligible):continue
            # Stay on the observed side of the visible surface; no blind rear approach.
            side=np.asarray(robot[:2])-target
            eligible=[i for i in eligible if np.dot(xy[i]-target,side)>0 and
                      all(np.linalg.norm(xy[i]-np.asarray(previous)[:2])>=settings.get('approach_retry_separation_m',.45) for previous in excluded_approaches)]
            if not eligible:continue
            i=min(eligible,key=lambda i:cost[cells[i]]+abs(distance[i]-standoff))
            cid='approach_'+obj['id'];obj['approach_candidate_ids']=[cid]
            candidates.append({'id':cid,'kind':'approach','object_id':obj['id'],'position':[*xy[i].tolist(),1.],
                'yaw':math.atan2(target[1]-xy[i,1],target[0]-xy[i,0]),'reachable':True,'path_length_m':cost[cells[i]]})
        unknown=self.inside & ~self.occupied & ~(self.free if self.inspected is None else self.inspected)
        regions,_=label(unknown)
        sizes=np.bincount(regions.ravel());meaningful=unknown&(sizes[regions]>=settings.get('min_unknown_cells',10))
        # Observed viewpoints can stand back from a frontier inflation band.
        front=self.safe() & (distance_transform_edt(~meaningful)*self.res<=settings.get('viewpoint_radius_m',3.0))
        viable=[c for c in cells if front[c] and cost[c]>settings.get('min_travel_m',.45)]
        ranked=[]
        sample_step=max(1,int(math.ceil(.3/self.res)))
        for c in viable:
            # Subsample spatially for bounded CPU cost; exact geometry rechecked.
            if c[0]%sample_step or c[1]%sample_step:continue
            if any(np.linalg.norm(self.xy(c)-np.asarray(previous)[:2])<settings.get('explore_retry_separation_m',.6) for previous in excluded_explores):continue
            novelty=min((np.linalg.norm(self.xy(c)-p) for p in self.scan_positions),default=3.)
            if novelty < settings.get('min_viewpoint_separation_m',.7):continue
            gain,heading=self.visible_unknown_gain(c,meaningful,with_heading=True)
            if gain==0:continue
            visited=sum(n for other,n in self.visits.items() if np.linalg.norm(self.xy(c)-self.xy(other))<.8)
            # Diminishing information returns keep a large distant room from
            # suppressing every nearby viewpoint. Novelty remains a hard
            # separation constraint instead of another reward for long travel.
            score=gain**settings.get('gain_power',.5)/(1+settings.get('travel_cost_weight',2.)*cost[c])/(1+visited*4)
            ranked.append((score,c,gain,heading))
        chosen=[]
        for score,c,gain,heading in sorted(ranked,reverse=True):
            if any(np.linalg.norm(self.xy(c)-self.xy(other))<settings.get('candidate_separation_m',.6) for other in chosen):continue
            chosen.append(c);p=self.xy(c)
            candidates.append({'id':f'frontier_{c[0]}_{c[1]}','kind':'explore','position':[float(p[0]),float(p[1]),1.],
                'reachable':True,'path_length_m':cost[c],'information_gain_score':gain,'score':score,'inspection_yaw':heading})
            if len(chosen)>=settings.get('max_candidates',6):break
        return candidates


def rule_action(obs):
    base={'task_id':obs['task_id'],'observation_id':obs['observation_id']}
    targets=[o for o in obs['objects'] if o['category']==obs['target']['category'] and o['color']==obs['target']['color'] and o['confirmed'] and o['observation_age_s']<=obs.get('max_observation_age_s',2.)]
    for o in sorted(targets,key=lambda o:o['range_m']):
        if o['approach_candidate_ids']:
            return {**base,'action':'approach','object_id':o['id'],'candidate_id':o['approach_candidate_ids'][0],'reason_code':'confirmed_target'}
    if not obs['scan_completed']:return {**base,'action':'scan','reason_code':'observe_unknown'}
    candidates=[c for c in obs['candidates'] if c['kind']=='explore']
    if candidates:return {**base,'action':'explore','candidate_id':max(candidates,key=lambda c:c['score'])['id'],'reason_code':'explore_frontier'}
    return {**base,'action':'report','reason_code':'no_reachable_frontier'}


def refresh_selected_explore(action, pending, current, grid, position):
    """Top-K ranking changes are not obstacle changes. Recheck selected cell itself."""
    if action.get('action')!='explore':return False
    cid=action.get('candidate_id')
    if any(c['id']==cid for c in current['candidates']):return False
    old=next((c for c in pending['candidates'] if c['id']==cid and c['kind']=='explore'),None)
    if old is None:return False
    costs,_=grid.reachable(position)
    cell=grid.cell(old['position'])
    if cell not in costs:return False
    current['candidates'].append({**old,'reachable':True,'path_length_m':costs[cell]})
    return True

def validate_action(action,obs):
    if not isinstance(action,dict):raise ValueError('action must be object')
    allowed={'task_id','observation_id','action','object_id','candidate_id','reason_code'}
    if set(action)-allowed:raise ValueError('unknown action fields')
    if action.get('task_id')!=obs['task_id'] or type(action.get('observation_id')) is not int or action.get('observation_id')!=obs['observation_id']:raise ValueError('stale task/observation')
    kind=action.get('action')
    if kind not in ('scan','explore','approach','hold','report'):raise ValueError('unsupported action')
    if not isinstance(action.get('reason_code'),str) or len(action['reason_code'])>100:raise ValueError('invalid reason')
    if kind in ('explore','approach'):
        if not isinstance(action.get('candidate_id'),str):raise ValueError('missing candidate_id: copy an ID from candidates for '+kind)
        candidates={c['id']:c for c in obs['candidates']};c=candidates.get(action.get('candidate_id'))
        if not c or not c['reachable'] or c['kind']!=kind:raise ValueError('invalid candidate')
        if kind=='approach':
            o=next((o for o in obs['objects'] if o['id']==action.get('object_id')),None)
            if not o or c.get('object_id')!=o['id'] or not o['confirmed'] or o['observation_age_s']>obs.get('max_observation_age_s',2.):raise ValueError('invalid object')
            if o['category']!=obs['target']['category'] or o['color']!=obs['target']['color']:raise ValueError('wrong target')
    elif 'candidate_id' in action or 'object_id' in action:raise ValueError('unexpected references')
    if kind=='report' and (not obs.get('scan_completed',False) or any(c.get('reachable') and c['kind']=='explore' for c in obs['candidates'])):
        raise ValueError('premature report: scan or explore reachable candidates before giving up')
    return action
