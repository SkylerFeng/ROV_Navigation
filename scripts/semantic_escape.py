"""Bounded escape from *inflation*, never from actual occupied geometry.
A circular swept envelope uses the yaw-independent circumscribed hull radius.
"""
import numpy as np
from scipy.spatial import cKDTree

def inflation_escape(grid,position,hull_radius=.373,max_distance=.65):
    root=grid.cell(position)
    if not grid.valid(root) or not grid.free[root] or grid.occupied[root] or grid.safe()[root]:return None
    # Include pool boundary and occupied-cell extent, not just their centres.
    obstacles=grid.origin+(np.argwhere(grid.occupied|~grid.inside)+.5)*grid.res
    tree=cKDTree(obstacles)
    margin=hull_radius+grid.res*np.sqrt(2)/2+.02
    start=np.asarray(position[:2]);initial=float(tree.query(start)[0])
    if initial<=margin:return None
    costs,_=grid.reachable(position)
    choices=[]
    for cell,d in costs.items():
        point=grid.xy(cell);length=float(np.linalg.norm(point-start))
        if not .2<=length<=max_distance or d>max_distance*1.5:continue
        line=start+(point-start)*np.linspace(0,1,max(2,int(length/.025)+1))[:,None]
        if not all(grid.valid(grid.cell(p)) and grid.free[grid.cell(p)] for p in line):continue
        clearances=tree.query(line)[0]
        if np.min(clearances)<margin or np.min(np.diff(clearances))<-.002:continue
        choices.append((float(clearances[-1])-length*.2,point,float(np.min(clearances))))
    if not choices:return None
    _,goal,clearance=max(choices,key=lambda item:item[0])
    return {'position':[float(goal[0]),float(goal[1]),float(position[2])],
            'swept_min_obstacle_center_distance_m':clearance,'required_distance_m':margin,
            'reason':'measured_pose_inside_conservative_inflation'}

def escape_segment_clear(grid,start,goal,hull_radius=.373):
    start=np.asarray(start[:2]);goal=np.asarray(goal[:2])
    length=float(np.linalg.norm(goal-start))
    line=start+(goal-start)*np.linspace(0,1,max(2,int(length/.025)+1))[:,None]
    if not all(grid.valid(grid.cell(p)) and grid.free[grid.cell(p)] for p in line):return False
    occupied=grid.origin+(np.argwhere(grid.occupied|~grid.inside)+.5)*grid.res
    minimum=float(cKDTree(occupied).query(line)[0].min())
    return minimum>hull_radius+grid.res*np.sqrt(2)/2+.02
