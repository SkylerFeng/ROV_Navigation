"""Audit recorded route against original triangles and the demo obstacle."""
import argparse,json
from pathlib import Path
import numpy as np
from pxr import Usd,UsdGeom
from validate_highbay_scene import point_triangle_distance,world_points
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
d=json.loads((a.directory/'motion.json').read_text())
s=Usd.Stage.Open(d['source_asset'])
prim=s.GetPrimAtPath('/Platform/Collision/Platform_collision_clean/mesh')
v,_=world_points(prim)
tri=v[np.array(UsdGeom.Mesh(prim).GetFaceVertexIndicesAttr().Get()).reshape(-1,3)]
radius=float(np.linalg.norm(d['hydrodynamics']['hull_size_m'])/2)
clearances=[]
# Recorded samples at <=0.25 second intervals; a sampled check, not a continuous proof.
for sample in d['samples'][::15]:
 center=np.array(sample['position'])+d['hydrodynamics']['center_of_mass_body_m']
 selected=tri[np.all(tri.max(1)>=center-1.,axis=1)&np.all(tri.min(1)<=center+1.,axis=1)]
 clearances.append(float(point_triangle_distance(center,selected).min()-radius) if len(selected) else 1.-radius)
checks={'goal_reached':bool(d['completed'] and d['final_error_m']<.08),
        'no_contact_reports':not d['contacts'],
        'scan_sphere_clearance_positive':min(clearances)>0,
        'obstacle_hull_clearance_positive':d['min_obstacle_hull_clearance_m']>0,
        'fully_submerged':d['min_submerged_fraction']>.99}
report={'passed':all(checks.values()),'checks':checks,'sampled_scan_sphere_clearance_m':min(clearances),'sample_interval_s':.25}
(a.directory/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if not report['passed']: raise SystemExit(1)
