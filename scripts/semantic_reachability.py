"""Observed-space Dijkstra with identical corner and inflation-escape constraints."""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

def reachable(grid,start):
    root=grid.cell(start);safe=grid.safe()
    if not grid.valid(root) or not grid.free[root] or grid.occupied[root]:return {},{}
    shape=grid.shape;size=int(np.prod(shape));ids=np.arange(size).reshape(shape)
    clearance=grid.obstacle_clearance();observed=grid.free&~grid.occupied&grid.inside
    edges={}
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
        target=np.roll(observed,(-dx,-dy),(0,1))
        target_safe=np.roll(safe,(-dx,-dy),(0,1))
        target_clear=np.roll(clearance,(-dx,-dy),(0,1))
        allowed=observed&target&(target_safe|(~safe&(target_clear>=clearance-1e-9)))
        if dx>0:allowed[-dx:,:]=False
        if dx<0:allowed[:-dx,:]=False
        if dy>0:allowed[:,-dy:]=False
        if dy<0:allowed[:,:-dy]=False
        edges[dx,dy]=allowed
    rows=[];cols=[];weights=[]
    for (dx,dy),allowed in edges.items():
        if dx and dy:allowed=allowed&edges[dx,0]&edges[0,dy]
        src=ids[allowed];dst=src+dx*shape[1]+dy
        rows.append(src);cols.append(dst);weights.append(np.full(len(src),np.hypot(dx,dy)*grid.res))
    graph=csr_matrix((np.concatenate(weights),(np.concatenate(rows),np.concatenate(cols))),shape=(size,size))
    dist,pred=dijkstra(graph,directed=True,indices=root[0]*shape[1]+root[1],return_predecessors=True)
    reached=np.flatnonzero(np.isfinite(dist));parents={}
    for idx in reached:
        if pred[idx]>=0:parents[divmod(int(idx),shape[1])]=divmod(int(pred[idx]),shape[1])
    costs={divmod(int(idx),shape[1]):float(dist[idx]) for idx in reached if safe.ravel()[idx]}
    return costs,parents
