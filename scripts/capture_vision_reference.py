"""Offline same-frame OceanSim pre/post optical degradation pairs.
The reference still includes scene materials, water surface and lighting.
Never publishes clear images or semantic truth to navigation.
"""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError('Choose a fresh capture directory')
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
try:
    import numpy as np
    import carb
    from PIL import Image
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
    import omni.replicator.core as rep
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleXFormPrim
    from isaacsim.core.utils.stage import open_stage
    from isaacsim.core.utils.semantics import add_update_semantics
    import isaacsim
    isaacsim.__path__.append('/home/ache/isaac-sim/extsUser/OceanSim/isaacsim')
    from isaacsim.oceansim.sensors.UW_Camera import UW_Camera
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((a.run/'manifest.json').read_text());scene=Path(manifest['scene'])
    if not scene.is_absolute():scene=root/scene
    with np.load(a.run/'semantic/latest_sensor.npz') as d:cp=d['cp'];cq=d['cq'];k=d['k'];shape=d['rgb'].shape
    events=[json.loads(x) for x in (a.run/'semantic/events.jsonl').read_text().splitlines()]
    last=next(e for e in reversed(events) if e['event']=='perception')['sim_time']
    controls=json.loads((a.run/'sim/controls.json').read_text())
    control=min(controls,key=lambda c:abs(c['t']-last))
    result=json.loads((a.run/'semantic/result.json').read_text())
    position=min(result['path'],key=lambda p:abs(p[0]-last))[1:4]
    carb.settings.get_settings().set('/rtx/raytracing/fractionalCutoutOpacity',True)
    open_stage(str(scene));world=World(stage_units_in_meters=1.,physics_dt=1/60,rendering_dt=1/30)
    body=world.stage.GetPrimAtPath('/World/ROV')
    UsdPhysics.RigidBodyAPI(body).GetRigidBodyEnabledAttr().Set(False)
    robot=world.scene.add(SingleXFormPrim('/World/ROV',name='validation_rov'))
    for path in ('/World/Markers',):
        prim=world.stage.GetPrimAtPath(path)
        if prim.IsValid():UsdGeom.Imageable(prim).MakeInvisible()
    truth=json.loads(scene.with_suffix('.truth.json').read_text())
    for o in truth['objects']:
        prim=world.stage.GetPrimAtPath('/World/SemanticObjects/'+o['id'])
        if prim.IsValid():add_update_semantics(prim,o['category'])
    cam=UW_Camera('/World/VisionReferenceCamera',resolution=(shape[1],shape[0]))
    world.reset();robot.set_world_pose(np.asarray(position),np.asarray(control['orientation']))
    cam.set_focal_length(cam.get_horizontal_aperture()*float(k[0,0])/shape[1]);cam.set_clipping_range(.08,15.)
    cam.initialize(viewport=False,max_range=8.)
    cam.set_world_pose(cp,cq,camera_axes='ros')
    annot=rep.AnnotatorRegistry.get_annotator('instance_segmentation',init_params={'colorize':False});annot.attach(cam._render_product_path)
    for _ in range(60):world.render()
    cam.render()
    # No world.render between reads: reference and degraded images share the input buffer.
    clear=cam._rgba_annot.get_data().numpy()[:,:,:3].copy();rgb=cam._uw_frame[:,:,:3].copy()
    depth=cam._depth_annot.get_data().numpy().copy()
    segmentation=annot.get_data();mask=np.asarray(segmentation['data']);labels=segmentation['info']['idToLabels']
    objects=[];masks={}
    for o in truth['objects']:
        ids=[int(i) for i,label in labels.items() if '/World/SemanticObjects/'+o['id'] in str(label)]
        visible=np.isin(mask,ids);ys,xs=np.where(visible)
        if len(xs)<35:continue
        masks[o['id']]=visible
        objects.append({'id':o['id'],'category':o['category'],'color':o['color'],'pixels':len(xs),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]})
    a.output.mkdir(parents=True)
    np.savez_compressed(a.output/'paired.npz',reference=clear,rgb=rgb,depth=depth,k=cam.get_intrinsics_matrix(),cp=cp,cq=cq)
    np.savez_compressed(a.output/'object_masks.npz',**masks)
    Image.fromarray(clear).save(a.output/'reference.png');Image.fromarray(rgb).save(a.output/'underwater.png')
    meta={'scene':str(scene),'source_run':str(a.run),'view_time':last,'objects':objects,
          'rigid_body_disabled_for_static_capture':True,
          'robot_position':robot.get_world_pose()[0].tolist(),
          'reference':'Same rendered LdrColor before OceanSim UW_render; not an in-air ground-truth photograph. Re-rendered historical viewpoint, not identical historical exposure.',
          'attenuation_rgb':list(cam._atten_coeff),'backscatter_rgb':list(cam._backscatter_coeff),'veiling_rgb':list(cam._backscatter_value),
          'sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [scene,root/'scripts/capture_vision_reference.py']}}
    (a.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print('PAIR_CAPTURED',str(a.output),objects,flush=True)
finally:app.close()
