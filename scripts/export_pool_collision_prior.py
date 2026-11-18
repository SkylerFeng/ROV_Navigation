"""Offline known-static-pool map. Never reads semantic object truth.
Clip collider triangles to the configured navigation height slab, conservatively
rasterize their XY projection. This is explicitly a map prior, NOT camera sensing.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from pxr import Usd,UsdGeom
p=argparse.ArgumentParser();p.add_argument('--resolution',type=float,default=.1);p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
prim_path='/World/Environment/Platform/Collision/Platform_collision_clean/mesh';stage=Usd.Stage.Open(str(a.scene));prim=stage.GetPrimAtPath(prim_path);mesh=UsdGeom.Mesh(prim)
pts=np.asarray(mesh.GetPointsAttr().Get());matrix=np.asarray(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()));pts=(np.c_[pts,np.ones(len(pts))]@matrix)[:,:3]
indices=np.asarray(mesh.GetFaceVertexIndicesAttr().Get());counts=np.asarray(mesh.GetFaceVertexCountsAttr().Get());assert np.all(counts==3)
triangles=pts[indices.reshape(-1,3)];zmin,zmax=.84,1.28;res=a.resolution
if res<=0:raise ValueError("resolution must be positive")
triangles=triangles[(triangles[:,:,2].max(1)>=zmin)&(triangles[:,:,2].min(1)<=zmax)]
def clip(poly,z,above):
 out=[]
 for v,w in zip(poly,poly[1:]+poly[:1]):
  vin=(v[2]>=z if above else v[2]<=z);win=(w[2]>=z if above else w[2]<=z)
  if vin:out.append(v)
  if vin!=win:out.append(v+(w-v)*((z-v[2])/(w[2]-v[2])))
 return out
cells=set()
for tri in triangles:
 poly=clip(clip(list(tri),zmin,True),zmax,False)
 if not poly:continue
 poly=np.asarray(poly)[:,:2];lo=np.floor((poly.min(0)-res)/res).astype(int);hi=np.ceil((poly.max(0)+res)/res).astype(int)
 xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));ij=np.column_stack([xx.ravel(),yy.ravel()]);q=(ij+.5)*res
 inside=np.zeros(len(q),bool);near=np.zeros(len(q),bool)
 for v,w in zip(poly,np.roll(poly,-1,axis=0)):
  edge=w-v;t=np.clip(((q-v)*edge).sum(1)/max(float(edge@edge),1e-20),0,1);near|=np.linalg.norm(q-v-t[:,None]*edge,axis=1)<=res*.707107
  if abs(w[1]-v[1])>1e-12:inside^=((v[1]>q[:,1])!=(w[1]>q[:,1]))&(q[:,0]<(w[0]-v[0])*(q[:,1]-v[1])/(w[1]-v[1])+v[0])
 cells.update(map(tuple,ij[near|inside]))
a.output.parent.mkdir(parents=True,exist_ok=True);xy=(np.asarray(sorted(cells))+.5)*res
np.savez_compressed(a.output,xy=xy,res=res,z_min=zmin,z_max=zmax)
meta={'source':'known static pool collider prior, not sensor-derived','scene':str(a.scene),'prim':prim_path,'cells':len(xy),'clipped_triangles':len(triangles),'z_slab':[zmin,zmax],'resolution_m':res,'collider_world_geometry_sha256':hashlib.sha256(pts.tobytes()+indices.tobytes()).hexdigest(),'semantic_objects_included':False}
a.output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
