"""Deterministic independent USD layers; truth metadata is offline-only."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def vec(v):return '('+', '.join(str(float(x)) for x in v)+')'
def build():
    cases=json.loads((ROOT/'config/semantic/complex_scenes.json').read_text());suite=[]
    for case in cases:
        lines=['#usda 1.0','(defaultPrim = "World" subLayers = [@pool_platform_semantic.usda@])',
               'over "World" {',' over "SemanticObjects" {']
        for name,category,color,pos,yaw in case['objects']:
            lines.extend([f'  over "{name}" {{',f'   double3 xformOp:translate = {vec(pos)}',f'   float xformOp:rotateZ = {float(yaw)}','  }'])
        for o in case['obstacles']:
            lines.extend([f'  def Cube "{o["name"]}" (prepend apiSchemas = ["PhysicsCollisionAPI"]) {{',
                '   double size = 1','   color3f[] primvars:displayColor = [(0.25, 0.28, 0.3)]',
                f'   double3 xformOp:translate = {vec(o["position"])}',f'   float3 xformOp:scale = {vec(o["size"])}',
                '   uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]','  }'])
        lines+=[' }','}']
        stem='pool_platform_semantic_complex_'+case['name'];scene=ROOT/'scenes'/(stem+'.usda')
        # Metadata properties must be on separate lines for USD grammar.
        lines[1]='(\n defaultPrim = "World"\n subLayers = [@pool_platform_semantic.usda@]\n)'
        scene.write_text('\n'.join(lines)+'\n')
        truth={'runtime_access':'forbidden: offline evaluation labels only',
               'objects':[dict(zip(['id','category','color','position','yaw'],o)) for o in case['objects']],
               'obstacles':case['obstacles']}
        scene.with_suffix('.truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        suite.append({'name':case['name'],'scene':str(scene.relative_to(ROOT)),'instruction':case['instruction'],
                      'search_region':case['search_region'],'task_config':'config/semantic/complex_task.json','wall_limit':850})
    (ROOT/'config/semantic/complex_suite.json').write_text(json.dumps(suite,ensure_ascii=False,indent=2)+'\n')
    print('Built',len(cases),'independent scenes')
if __name__=='__main__':build()
