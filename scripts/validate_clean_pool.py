"""Audit clean-pool composition and water/physics coordinate agreement."""
import json
import numpy as np
from pxr import Ar, Usd, UsdGeom, UsdPhysics, UsdUtils
import os
from pathlib import Path
from experiment import ROOT, load_experiment
from hydrodynamics import Hydrodynamics

c = load_experiment('clean_pool')
s = Usd.Stage.Open(c['scene_file'])
water = s.GetPrimAtPath('/World/Water')
surface = UsdGeom.Mesh(s.GetPrimAtPath('/World/Water/Surface'))
transform = UsdGeom.XformCache().GetLocalToWorldTransform(water)
raw = water.GetAttribute('oceansim:water:boundaryXY').Get()
height = water.GetAttribute('oceansim:water:surfaceZ').Get()
world_boundary = np.asarray([transform.Transform((float(x),float(y),height)) for x,y in raw])
boundary = json.loads((ROOT/c['water_boundary']).read_text())
points = np.asarray(surface.GetPointsAttr().Get(), dtype=float)
world_points = np.asarray([transform.Transform(tuple(p)) for p in points])
collider = s.GetPrimAtPath(c['collision_prim'])
mdl = Path(os.environ.get('ISAAC_SIM_PATH','/home/ache/isaac-sim'))/'kit/mdl/core/Base'
context = Ar.ResolverContext(Ar.DefaultResolverContext([str(mdl)]))
with Ar.ResolverContextBinder(context):
    _, _, missing = UsdUtils.ComputeAllDependencies(c['scene_file'])
dynamics = Hydrodynamics(c['hydrodynamics'],c['water_surface'],c['pool_floor'],boundary)
checks = {
 'metres_z_up': UsdGeom.GetStageMetersPerUnit(s)==1 and UsdGeom.GetStageUpAxis(s)=='Z',
 'no_missing_dependencies': not missing,
 'no_scanned_platform_layers': not any('Platform.final' in l.identifier or 'HighBay' in l.identifier for l in s.GetUsedLayers()),
 'water_boundary_matches_world_metadata': np.allclose(world_boundary[:,:2],boundary,atol=1e-6),
 'water_mesh_at_physics_surface': np.allclose(world_points[:,2],c['water_surface']),
 'bottom_matches_metadata': abs(water.GetAttribute('oceansim:water:bottomZ').Get()+c['source_to_world'][2]-c['pool_floor'])<1e-6,
 'static_pool_collider': collider.HasAPI(UsdPhysics.CollisionAPI) and not collider.HasAPI(UsdPhysics.RigidBodyAPI),
 'water_without_collision': not any(p.HasAPI(UsdPhysics.CollisionAPI) for p in Usd.PrimRange(water)),
 'start_and_goal_fully_submerged': all(dynamics.submersion(p,np.eye(3))>.999 for p in (c['start'],c['goal'])),
 'hydrodynamics_selected':c['physics_mode']=='hydrodynamics',
}
report={'passed':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},
        'water_world_bounds':[world_points.min(axis=0).tolist(),world_points.max(axis=0).tolist()],
        'missing_dependencies':list(missing), 'note':'Engineered pool follows supplied Tile3 polygon; no claim of scanned wall registration.'}
output=ROOT/'logs/clean_pool_static_audit.json'
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['passed']
