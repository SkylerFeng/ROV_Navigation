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
    def __init__(self,boundary,resolution=.15,clearance=.5):
        from matplotlib.path import Path
        self.res=float(resolution);self.clearance=float(clearance)
        boundary=np.asarray(boundary);self.origin=np.floor((boundary.min(0)-1)/self.res)*self.res
        shape=np.ceil((boundary.max(0)+1-self.origin)/self.res).astype(int)
        self.shape=tuple(shape);cells=np.indices(self.shape).reshape(2,-1).T
        self.inside=Path(boundary).contains_points(self.origin+(cells+.5)*self.res).reshape(self.shape)
        self.free=np.zeros(self.shape,bool);self.occupied=np.zeros(self.shape,bool);self.visits={};self.scan_positions=[]
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
        ends=pts[(pts[:,2]>.84)&(pts[:,2]<1.28)]
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
        if not self.valid(root) or not safe[root]:return cost,parent
        cost[root]=0.;queue=[(0.,root)]
        while queue:
            d,c=heapq.heappop(queue)
            if d>cost[c]:continue
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                v=(c[0]+dx,c[1]+dy)
                if not self.valid(v) or not safe[v]:continue
                if dx and dy and not(safe[c[0]+dx,c[1]] and safe[c[0],c[1]+dy]):continue
                nd=d+math.hypot(dx,dy)*self.res
                if nd<cost.get(v,float('inf')):cost[v]=nd;parent[v]=c;heapq.heappush(queue,(nd,v))
        return cost,parent
    def mark_scanned(self,position):
        self.scan_positions.append(np.asarray(position[:2],float))

    def visible_unknown_gain(self,cell,meaningful):
        # Count unknown cells reachable by sight without crossing an observed wall.
        visible=set()
        for angle in np.linspace(-np.pi,np.pi,48,endpoint=False):
            direction=np.array([np.cos(angle),np.sin(angle)])
            for distance in np.arange(self.res,3.01,self.res):
                c=self.cell(self.xy(cell)+direction*distance)
                if not self.valid(c) or not self.inside[c] or self.occupied[c]:break
                if not self.free[c]:
                    if meaningful[c]:visible.add(c)
                    break
        return len(visible)

    def candidates(self,robot,objects,standoff=.8):
        cost,parent=self.reachable(robot);candidates=[]
        if not cost:return candidates
        cells=list(cost);xy=np.array([self.xy(c) for c in cells])
        for obj in objects:
            if not obj['confirmed'] or obj['observation_age_s']>2.:continue
            target=np.array(obj['surface_world'][:2]);distance=np.linalg.norm(xy-target,axis=1)
            eligible=np.flatnonzero((distance>=standoff)&(distance<=standoff+.28))
            if not len(eligible):continue
            # Stay on the observed side of the visible surface; no blind rear approach.
            side=np.asarray(robot[:2])-target
            eligible=[i for i in eligible if np.dot(xy[i]-target,side)>0]
            if not eligible:continue
            i=min(eligible,key=lambda i:cost[cells[i]]+abs(distance[i]-standoff))
            cid='approach_'+obj['id'];obj['approach_candidate_ids']=[cid]
            candidates.append({'id':cid,'kind':'approach','object_id':obj['id'],'position':[*xy[i].tolist(),1.],
                'yaw':math.atan2(target[1]-xy[i,1],target[0]-xy[i,0]),'reachable':True,'path_length_m':cost[cells[i]]})
        unknown=self.inside & ~self.free & ~self.occupied
        regions,_=label(unknown)
        sizes=np.bincount(regions.ravel());meaningful=unknown&(sizes[regions]>=10)
        # Observed viewpoints can stand back from a frontier inflation band.
        front=self.safe() & (distance_transform_edt(~meaningful)*self.res<=3.0)
        viable=[c for c in cells if front[c] and cost[c]>.45]
        ranked=[]
        for c in viable:
            # Subsample spatially for bounded CPU cost; exact geometry rechecked.
            if c[0]%2 or c[1]%2:continue
            novelty=min((np.linalg.norm(self.xy(c)-p) for p in self.scan_positions),default=3.)
            if novelty < .7:continue
            gain=self.visible_unknown_gain(c,meaningful)
            if gain==0:continue
            visited=sum(n for other,n in self.visits.items() if np.linalg.norm(self.xy(c)-self.xy(other))<.8)
            score=gain*min(novelty,2.)/(1+.25*cost[c])/(1+visited*4)
            ranked.append((score,c,gain))
        chosen=[]
        for score,c,gain in sorted(ranked,reverse=True):
            if any(np.linalg.norm(self.xy(c)-self.xy(other))<.6 for other in chosen):continue
            chosen.append(c);p=self.xy(c)
            candidates.append({'id':f'frontier_{c[0]}_{c[1]}','kind':'explore','position':[float(p[0]),float(p[1]),1.],
                'reachable':True,'path_length_m':cost[c],'information_gain_score':gain,'score':score})
            if len(chosen)>=6:break
        return candidates


def rule_action(obs):
    base={'task_id':obs['task_id'],'observation_id':obs['observation_id']}
    targets=[o for o in obs['objects'] if o['category']==obs['target']['category'] and o['color']==obs['target']['color'] and o['confirmed'] and o['observation_age_s']<=2.]
    for o in sorted(targets,key=lambda o:o['range_m']):
        if o['approach_candidate_ids']:
            return {**base,'action':'approach','object_id':o['id'],'candidate_id':o['approach_candidate_ids'][0],'reason_code':'confirmed_target'}
    if not obs['scan_completed']:return {**base,'action':'scan','reason_code':'observe_unknown'}
    candidates=[c for c in obs['candidates'] if c['kind']=='explore']
    if candidates:return {**base,'action':'explore','candidate_id':max(candidates,key=lambda c:c['score'])['id'],'reason_code':'explore_frontier'}
    return {**base,'action':'report','reason_code':'no_reachable_frontier'}


def validate_action(action,obs):
    if not isinstance(action,dict):raise ValueError('action must be object')
    allowed={'task_id','observation_id','action','object_id','candidate_id','reason_code'}
    if set(action)-allowed:raise ValueError('unknown action fields')
    if action.get('task_id')!=obs['task_id'] or type(action.get('observation_id')) is not int or action.get('observation_id')!=obs['observation_id']:raise ValueError('stale task/observation')
    kind=action.get('action')
    if kind not in ('scan','explore','approach','hold','report'):raise ValueError('unsupported action')
    if not isinstance(action.get('reason_code'),str) or len(action['reason_code'])>100:raise ValueError('invalid reason')
    if kind in ('explore','approach'):
        candidates={c['id']:c for c in obs['candidates']};c=candidates.get(action.get('candidate_id'))
        if not c or not c['reachable'] or c['kind']!=kind:raise ValueError('invalid candidate')
        if kind=='approach':
            o=next((o for o in obs['objects'] if o['id']==action.get('object_id')),None)
            if not o or c.get('object_id')!=o['id'] or not o['confirmed'] or o['observation_age_s']>2.:raise ValueError('invalid object')
            if o['category']!=obs['target']['category'] or o['color']!=obs['target']['color']:raise ValueError('wrong target')
    elif 'candidate_id' in action or 'object_id' in action:raise ValueError('unexpected references')
    return action
