"""Fixed-layout offline capture: pipe end/side views and naturally occluded boxes.
Scene transforms are never changed or saved. Instance truth is offline only.
"""
import argparse,json,math,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--case',required=True,choices=['west_baffles','east_equipment','wrong_hint_box']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError(a.output)
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
try:
 import numpy as np,carb
 from PIL import Image
 from pxr import UsdGeom
 import omni.replicator.core as rep
 from isaacsim.core.api import World
 from isaacsim.core.utils.stage import open_stage
 from isaacsim.core.utils.semantics import add_update_semantics
 import isaacsim
 isaacsim.__path__.append('/home/ache/isaac-sim/extsUser/OceanSim/isaacsim')
 from isaacsim.oceansim.sensors.UW_Camera import UW_Camera
 from build_semantic_scene import ROOT,inspection_light
 from build_scene import translate
 scene=ROOT/'scenes'/('pool_platform_semantic_complex_'+a.case+'.usda');truth=json.loads(scene.with_suffix('.truth.json').read_text());scene_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
 carb.settings.get_settings().set('/rtx/raytracing/fractionalCutoutOpacity',True)
 open_stage(str(scene));world=World(stage_units_in_meters=1.,physics_dt=1/60,rendering_dt=1/30);stage=world.stage
 stage.GetPrimAtPath('/World/ROV').SetActive(False)
 for o in truth['objects']:add_update_semantics(stage.GetPrimAtPath('/World/SemanticObjects/'+o['id']),o['category'])
 cam=UW_Camera('/World/HardcaseCamera',resolution=(640,360));lamp=inspection_light(stage,'/World/HardcaseLight',[0,0,1.])
 world.reset();cam.initialize(viewport=False,max_range=8);cam.set_focal_length(cam.get_horizontal_aperture()/2);cam._camera_k=cam.get_intrinsics_matrix()
 annot=rep.AnnotatorRegistry.get_annotator('instance_segmentation',init_params={'colorize':False});annot.attach(cam._render_product_path)
 a.output.mkdir(parents=True);rows=[]
 for split in ('train','val','test'):
  for kind in ('images','labels'):(a.output/kind/split).mkdir(parents=True)
 for oi,o in enumerate(truth['objects']):
  target=np.asarray(o['position']);base=math.radians(o['yaw'])
  for angle_i in range(12):
   # Hold out entire wrong-hint layout, including its misleading yellow pipe.
   split='test' if a.case=='wrong_hint_box' else ('val' if angle_i in (2,8) else 'train')
   for ri,radius in enumerate((.9,1.5,2.3)):
    angle=base+angle_i*math.pi/6;cp=target+np.array([radius*math.cos(angle),radius*math.sin(angle),-.05]);yaw=angle+math.pi
    cam.set_world_pose(cp,np.array([math.cos(yaw/2),0,0,math.sin(yaw/2)]),camera_axes='world');translate(lamp,cp+.05*np.array([math.cos(yaw),math.sin(yaw),.4]))
    for _ in range(12 if rows else 60):world.render()
    cam.render();data=annot.get_data();mask=np.asarray(data['data']);labels=data['info']['idToLabels'];lines=[];visible=[]
    for obj in truth['objects']:
     ids=[int(i) for i,label in labels.items() if '/World/SemanticObjects/'+obj['id'] in str(label)];ys,xs=np.where(np.isin(mask,ids))
     if len(xs)<35:continue
     x0,x1=xs.min(),xs.max()+1;y0,y1=ys.min(),ys.max()+1
     if min(x1-x0,y1-y0)<6:continue
     lines.append(f"{0 if obj['category']=='pipe' else 1} {(x0+x1)/1280:.6f} {(y0+y1)/720:.6f} {(x1-x0)/640:.6f} {(y1-y0)/360:.6f}")
     visible.append({'id':obj['id'],'pixels':len(xs),'bbox':[int(x0),int(y0),int(x1),int(y1)]})
    name=f'{a.case}_{oi}_{angle_i}_{ri}';Image.fromarray(cam._uw_frame[:,:,:3]).save(a.output/'images'/split/(name+'.png'));(a.output/'labels'/split/(name+'.txt')).write_text('\n'.join(lines))
    rows.append({'id':name,'split':split,'focus':o['id'],'angle_relative_deg':angle_i*30,'radius_m':radius,'camera_position':cp.tolist(),'visible':visible})
  print('CAPTURED',o['id'],len(rows),flush=True)
 (a.output/'manifest.json').write_text(json.dumps({'scene':str(scene),'scene_sha256':scene_hash,'note':'Fixed scene; offline camera sweeps can include blocked/non-navigable viewpoints. Wrong-hint layout is held-out test only; training/validation views share layouts, not independent generalization.','rows':rows},indent=2))
 assert hashlib.sha256(scene.read_bytes()).hexdigest()==scene_hash
finally:app.close()
