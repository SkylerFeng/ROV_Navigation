"""Independent Highbay semantic scene. Source poses are evaluation-only."""
import json
from pathlib import Path
import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, UsdLux
from build_scene import translate
ROOT=Path(__file__).resolve().parents[1]
COLORS={'yellow':(.95,.75,.03),'blue':(.03,.15,.85),'red':(.8,.04,.04)}
def add_object(stage,name,category,color,position,yaw=0):
    path='/World/SemanticObjects/'+name
    if category=='pipe':
        shape=UsdGeom.Mesh.Define(stage,path);vertices=[]
        for x,r in [(-.325,.13),(.325,.13),(-.325,.09),(.325,.09)]:
            vertices.extend([(x,r*np.cos(a),r*np.sin(a)) for a in np.linspace(0,2*np.pi,32,endpoint=False)])
        faces=[]
        for a,b in [(0,32),(64,96),(0,64),(32,96)]:
            for i in range(32):
                j=(i+1)%32;faces.extend([a+i,a+j,b+j,b+i])
        shape.CreatePointsAttr(vertices);shape.CreateFaceVertexCountsAttr([4]*(len(faces)//4))
        shape.CreateFaceVertexIndicesAttr(faces);shape.CreateSubdivisionSchemeAttr('none');shape.CreateDoubleSidedAttr(True)
    else:
        shape=UsdGeom.Cube.Define(stage,path);shape.CreateSizeAttr(1)

    translate(shape,position);shape.AddRotateZOp().Set(float(yaw))
    if category != "pipe":shape.AddScaleOp().Set(Gf.Vec3f(.38,.38,.38))
    shape.CreateDisplayColorAttr([Gf.Vec3f(*COLORS[color])])
    mat=UsdShade.Material.Define(stage,'/World/SemanticMaterials/'+color)
    shader=UsdShade.Shader.Define(stage,mat.GetPath().AppendChild('Surface'))
    shader.CreateIdAttr('UsdPreviewSurface');shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*COLORS[color]))
    shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.65)
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
    UsdShade.MaterialBindingAPI.Apply(shape.GetPrim()).Bind(mat)
    UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
    shape.GetPrim().CreateAttribute('semantic:category',Sdf.ValueTypeNames.String).Set(category)
    return shape.GetPrim()
def inspection_light(stage,path,position):
    light=UsdLux.SphereLight.Define(stage,path)
    light.CreateRadiusAttr(.04);light.CreateIntensityAttr(250.)
    light.CreateNormalizeAttr(True);light.CreateColorAttr(Gf.Vec3f(1.,.97,.92))
    translate(light,position)
    return light

def configure_water_appearance(stage):
    """Match the mixed scene's reflective water in this layer only."""
    path='/World/Environment/Platform/Water/Looks/Water/PreviewSurface'
    shader=UsdShade.Shader(stage.GetPrimAtPath(path))
    if not shader:
        raise RuntimeError('Missing embedded Highbay water shader: '+path)
    for name,value in [('ior',1.333),('opacity',.38),('roughness',.12)]:
        shader.CreateInput(name,Sdf.ValueTypeNames.Float).Set(value)
    shader.CreateInput('specularColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1.,1.,1.))
    # The base scene explicitly disables reflections through its specular
    # workflow. Restore the default dielectric workflow used by mixed.
    shader.CreateInput('useSpecularWorkflow',Sdf.ValueTypeNames.Int).Set(0)

def build():
    base=json.loads((ROOT/'config/scenarios.json').read_text())['platform_ego']
    config={**base,'title':'Highbay semantic search / component hydrodynamics','start':[-2.,0.,1.],'goal':[-2.,0.,1.],'obstacles':[],'display_water_opacity':.38}
    config.update(overview_eye=[-2.,-2.8,2.6],overview_target=[-2.,0.,1.3])
    (ROOT/'config/scenarios_semantic.json').write_text(json.dumps({'platform_semantic':config},ensure_ascii=False,indent=2)+chr(10))
    path=ROOT/'scenes/pool_platform_semantic.usda'
    stage=Usd.Stage.CreateNew(str(path));stage.GetRootLayer().subLayerPaths=['pool_platform_ego.usda']
    stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    configure_water_appearance(stage)
    UsdGeom.Imageable(stage.GetPrimAtPath('/World/Markers')).MakeInvisible()
    objects=[('YellowPipe','pipe','yellow',[-2.,-1.35,1.12],0),('BluePipe','pipe','blue',[.1,.85,1.12],25),('YellowBox','box','yellow',[.5,-.7,1.05],0),('RedBox','box','red',[-.6,1.,1.05],15)]
    for obj in objects:add_object(stage,*obj)
    inspection_light(stage,"/World/ROV/InspectionLight",[.35,0,.12])
    stage.GetRootLayer().Save()
    (ROOT/'config/semantic/evaluation_scene.json').write_text(json.dumps({'runtime_access':'forbidden: offline evaluation labels only','objects':[dict(zip(['id','category','color','position','yaw'],o)) for o in objects]},indent=2)+chr(10))
    print(path)
if __name__=='__main__':build()
