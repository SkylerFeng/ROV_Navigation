"""Render actual OceanSim RGB; visible instance masks generate YOLO boxes.
Layouts are disjoint across splits. Ground truth stays in this offline generator.
Run with Isaac python; stop other GPU simulations first.
"""
import argparse,json,math,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('logs/semantic_dataset_lit'));p.add_argument('--layouts',type=int,default=36);p.add_argument('--views',type=int,default=12);p.add_argument('--seed',type=int,default=41);a=p.parse_args()
if a.layouts<10 or a.views<4:raise ValueError('Use >=10 layouts and >=4 views')
if a.output.exists():raise FileExistsError('Choose a fresh dataset output directory')
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
try:
    import numpy as np
    from PIL import Image
    from pxr import UsdGeom,Gf
    import omni.replicator.core as rep
    from isaacsim.core.api import World
    from isaacsim.core.utils.stage import open_stage
    from isaacsim.core.utils.semantics import add_update_semantics
    import isaacsim
    isaacsim.__path__.append('/home/ache/isaac-sim/extsUser/OceanSim/isaacsim')
    from isaacsim.oceansim.sensors.UW_Camera import UW_Camera
    from build_semantic_scene import ROOT,add_object,inspection_light
    from build_scene import translate
    import carb
    carb.settings.get_settings().set('/rtx/raytracing/fractionalCutoutOpacity',True)
    open_stage(str(ROOT/'scenes/pool_platform_ego.usda'))
    world=World(stage_units_in_meters=1.,physics_dt=1/60,rendering_dt=1/30);stage=world.stage
    stage.GetPrimAtPath('/World/ROV').SetActive(False)
    UsdGeom.Imageable(stage.GetPrimAtPath('/World/Markers')).MakeInvisible()
    cam=UW_Camera('/World/DatasetCamera',resolution=(640,360))
    lamp=inspection_light(stage,"/World/DatasetLight",[0,0,1.])
    world.reset();cam.initialize(viewport=False,max_range=8)
    cam.set_focal_length(cam.get_horizontal_aperture()/2);cam._camera_k=cam.get_intrinsics_matrix()
    annot=rep.AnnotatorRegistry.get_annotator('instance_segmentation',init_params={'colorize':False});annot.attach(cam._render_product_path)
    objects=[]
    for i,(cat,col) in enumerate([('pipe','yellow'),('pipe','blue'),('box','yellow'),('box','red')]):
        prim=add_object(stage,'Object'+str(i),cat,col,[0,0,1.1]);add_update_semantics(prim,cat);objects.append((prim,cat,col))
    rng=np.random.default_rng(a.seed);rows=[];color_samples={c:[] for c in ['yellow','blue','red','background']}
    a.output.mkdir(parents=True,exist_ok=True)
    for split in ['train','val','test']:
        for folder in ['images','labels']:(a.output/folder/split).mkdir(parents=True,exist_ok=True)
    for layout in range(a.layouts):
        split='train' if layout<int(a.layouts*.7) else 'val' if layout<int(a.layouts*.85) else 'test'
        poses=[]
        for prim,cat,col in objects:
            pos=[rng.uniform(-2,2),rng.uniform(-1.1,1.1),rng.uniform(1.,1.16)];poses.append(pos)
            translate(prim,pos)
            for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
                if op.GetOpType()==UsdGeom.XformOp.TypeRotateZ:op.Set(float(rng.uniform(-180,180)))
        for view in range(a.views):
            target=np.array(poses[view%4]);angle=rng.uniform(-math.pi,math.pi);radius=rng.uniform(.85,3.)
            cp=target+np.array([radius*np.cos(angle),radius*np.sin(angle),rng.uniform(-.12,.1)])
            yaw=math.atan2(target[1]-cp[1],target[0]-cp[0])+rng.uniform(-.4,.4)
            if view==a.views-1:yaw+=math.pi # deliberate negative views
            cam.set_world_pose(cp,np.array([np.cos(yaw/2),0,0,np.sin(yaw/2)]),camera_axes='world')
            translate(lamp,cp+.05*np.array([np.cos(yaw),np.sin(yaw),.4]))
            for _ in range(8):world.render()
            cam.render();data=annot.get_data();mask=np.asarray(data['data']);labels=data['info']['idToLabels'];lines=[];object_pixels=np.zeros(mask.shape,bool)
            for prim,cat,col in objects:
                ids=[int(i) for i,label in labels.items() if str(prim.GetPath()) in str(label)]
                visible=np.isin(mask,ids);object_pixels|=visible;ys,xs=np.where(visible)
                if len(xs)<35:continue
                pixels=cam._uw_frame[ys,xs,:3]
                chosen=np.linspace(0,len(pixels)-1,min(300,len(pixels)),dtype=int)
                if split=='train':color_samples[col].append(pixels[chosen])
                x0,x1=xs.min(),xs.max()+1;y0,y1=ys.min(),ys.max()+1
                if min(x1-x0,y1-y0)<6:continue
                lines.append(f"{0 if cat=='pipe' else 1} {(x0+x1)/1280:.6f} {(y0+y1)/720:.6f} {(x1-x0)/640:.6f} {(y1-y0)/360:.6f}")
            if split=='train':
                background=cam._uw_frame[~object_pixels,:3]
                chosen=np.linspace(0,len(background)-1,min(600,len(background)),dtype=int)
                color_samples['background'].append(background[chosen])
            name=f'layout{layout:03d}_view{view:02d}'
            Image.fromarray(cam._uw_frame[:,:,:3]).save(a.output/'images'/split/(name+'.png'))
            (a.output/'labels'/split/(name+'.txt')).write_text(chr(10).join(lines))
            rows.append({'id':name,'layout':layout,'split':split,'labels':len(lines),'camera_position':cp.tolist()})
        print('Rendered layout',layout,split,'labels',sum(x['labels'] for x in rows if x['layout']==layout),flush=True)
    (a.output/'dataset.yaml').write_text('path: '+str(a.output.resolve())+chr(10)+'train: images/train'+chr(10)+'val: images/val'+chr(10)+'test: images/test'+chr(10)+'names: {0: pipe, 1: box}'+chr(10))
    np.savez_compressed(a.output/'color_samples.npz',**{c:np.concatenate(v) for c,v in color_samples.items()})
    (a.output/'manifest.json').write_text(json.dumps({'seed':a.seed,'source_scene':'pool_platform_ego.usda','renderer':'OceanSim UW_Camera','annotation':'visible instance masks','rows':rows},indent=2))
    print('Dataset completed:',len(rows),'frames',sum(r['labels'] for r in rows),'labels',flush=True)
finally:app.close()
