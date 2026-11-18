"""Vectorized visibility rays; same occupied/unknown semantics as ExplorationGrid."""
import math
import numpy as np
from functools import lru_cache

@lru_cache(maxsize=16)
def ray_pattern(res,limit):
    angles=np.linspace(-np.pi,np.pi,48,endpoint=False)
    distances=np.arange(res,limit+.01,res)
    offsets=np.stack([np.cos(angles),np.sin(angles)],axis=-1)[:,None,:]*distances[None,:,None]
    distinct=None
    delta=angles[:,None]-angles[None,:]
    sector=np.abs(np.arctan2(np.sin(delta),np.cos(delta)))<=math.pi/3
    return angles,offsets,distinct,sector

def visible_gain(grid,cell,meaningful,with_heading=False):
    angles,offsets,distinct,sector=ray_pattern(grid.res,grid.inspection_range or 3.)
    cells=np.floor((grid.xy(cell)[None,None,:]+offsets-grid.origin)/grid.res).astype(int)
    distinct=np.ones(cells.shape[:2],bool)
    distinct[:,1:]=np.any(cells[:,1:]!=cells[:,:-1],axis=-1)
    valid=(cells>=0).all(-1)&(cells<np.asarray(grid.shape)).all(-1)
    x=np.clip(cells[:,:,0],0,grid.shape[0]-1);y=np.clip(cells[:,:,1],0,grid.shape[1]-1)
    stopped=np.maximum.accumulate(~valid|~grid.inside[x,y]|grid.occupied[x,y],axis=1)
    selected=~stopped&meaningful[x,y]&distinct
    gain=int(np.unique(x[selected]*grid.shape[1]+y[selected]).size)
    if not with_heading:return gain
    ray_gains=selected.sum(1)
    scores=sector@ray_gains
    preferred=math.atan2(np.dot(ray_gains,np.sin(angles)),np.dot(ray_gains,np.cos(angles)))
    best=max(range(len(angles)),key=lambda i:(scores[i],math.cos(angles[i]-preferred)))
    return gain,float(angles[best])
