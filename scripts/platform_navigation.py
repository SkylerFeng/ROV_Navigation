"""Known-map 2-D A* at fixed depth with conservative swept-sphere clearance."""
import heapq
import math
import numpy as np
from hydrodynamics import inside_polygon
from validate_highbay_scene import point_triangle_distance


def plan(stage, boundary, start, goal, obstacles, radius=.40, spacing=.15):
    from pxr import UsdGeom
    prim = stage.GetPrimAtPath('/World/Pool/Collision/Platform_collision_clean/mesh')
    mesh = UsdGeom.Mesh(prim)
    points = np.array(mesh.GetPointsAttr().Get())
    matrix = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0))
    points = (np.c_[points,np.ones(len(points))] @ matrix)[:,:3]
    counts = np.array(mesh.GetFaceVertexCountsAttr().Get())
    if not np.all(counts==3): raise ValueError('Expected triangulated source collider')
    triangles = points[np.array(mesh.GetFaceVertexIndicesAttr().Get()).reshape(-1,3)]
    origin = np.array([2.,0.])
    shape = (41,24)
    center_z = start[2]+.116
    margin = radius+spacing*math.sqrt(2)/2
    low = np.array([*origin,center_z])-margin
    high = np.array([*(origin+(np.array(shape)-1)*spacing),center_z])+margin
    triangles = triangles[np.all(triangles.max(1)>=low,axis=1)&np.all(triangles.min(1)<=high,axis=1)]
    # Extra half-cell diagonal covers every point on adjacent-cell segments.
    margin = radius+spacing*math.sqrt(2)/2
    def clearance(xy):
        for angle in np.linspace(0,2*np.pi,16,endpoint=False):
            if not inside_polygon(xy+margin*np.array([np.cos(angle),np.sin(angle)]),boundary): return False
        for x,y,r in obstacles:
            if np.linalg.norm(xy-[x,y])<=r+margin: return False
        return not len(triangles) or point_triangle_distance(np.array([*xy,center_z]),triangles).min()>margin
    free = np.zeros(shape,dtype=bool)
    for node in np.ndindex(shape): free[node]=clearance(origin+np.array(node)*spacing)
    def cell(pos): return tuple(np.rint((np.array(pos[:2])-origin)/spacing).astype(int))
    first,last=cell(start),cell(goal)
    if not free[first] or not free[last]: raise RuntimeError('Start/goal lacks inflated clearance')
    costs={first:0.};parents={};queue=[(0.,first)]
    while queue:
        _,node=heapq.heappop(queue)
        if node==last: break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nxt=(node[0]+dx,node[1]+dy)
            if not (0<=nxt[0]<shape[0] and 0<=nxt[1]<shape[1] and free[nxt]): continue
            if dx and dy and not (free[node[0]+dx,node[1]] and free[node[0],node[1]+dy]): continue
            cost=costs[node]+math.hypot(dx,dy)
            if cost<costs.get(nxt,float('inf')):
                costs[nxt]=cost;parents[nxt]=node
                heapq.heappush(queue,(cost+math.dist(nxt,last),nxt))
    if last not in costs: raise RuntimeError('No safe route in demo planning region')
    route=[last]
    while route[-1]!=first: route.append(parents[route[-1]])
    route.reverse()
    waypoints=np.array([[*(origin+np.array(node)*spacing),start[2]] for node in route])
    # Align endpoints with actual lattice nodes so start connectors are safe.
    return waypoints, {'algorithm':'A* known static collision map, fixed depth',
                       'resolution_m':spacing,'inflation_radius_m':radius,
                       'segment_margin_m':margin,'free_cells':int(free.sum()),
                       'map_cells':int(free.size),'route_nodes':len(route),
                       'obstacles':obstacles,'bounds_xy':[origin.tolist(),(origin+(np.array(shape)-1)*spacing).tolist()]}
