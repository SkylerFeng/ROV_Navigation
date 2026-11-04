"""Evaluation-only layouts; navigation never imports these object positions."""
from pxr import Usd,UsdGeom,Gf
from build_scene import translate
from build_semantic_scene import ROOT,add_object

def build():
    for name,position in [('occluded',[1.2,-1.6,1.12]),('relocated',[-3.6,-1.4,1.12]),('screened',[-4.35,.25,1.12])]:
        p=ROOT/f'scenes/pool_platform_semantic_{name}.usda'
        s=Usd.Stage.CreateNew(str(p));s.GetRootLayer().subLayerPaths=['pool_platform_semantic.usda']
        s.SetDefaultPrim(s.GetPrimAtPath('/World'));translate(s.GetPrimAtPath('/World/SemanticObjects/YellowPipe'),position)
        if name=='occluded':
            prim=add_object(s,'Occluder','box','blue',[-.15,-.8,1.1],0)
            for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
                if op.GetOpType()==UsdGeom.XformOp.TypeScale:op.Set(Gf.Vec3f(.3,1.1,.8))
        if name=='screened':
            prim=add_object(s,'Screen','box','blue',[-3.25,.15,1.1],0)
            for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
                if op.GetOpType()==UsdGeom.XformOp.TypeScale:op.Set(Gf.Vec3f(.25,.8,.8))
        s.GetRootLayer().Save();print(p)
if __name__=='__main__':build()
