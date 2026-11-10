"""Offline evaluator must follow configured target, rotation and object shape."""
import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from analyze_semantic_trial import analyze,ROOT

class AuditTests(unittest.TestCase):
    def test_pipe_rotation_and_box_target(self):
        catalogue=json.loads((ROOT/'config/semantic/evaluation_scene.json').read_text())['objects']
        for target_id in ('BluePipe','RedBox'):
            target=next(o for o in catalogue if o['id']==target_id)
            angle=math.radians(target['yaw']);c,s=math.cos(angle),math.sin(angle)
            def world(local):
                return (np.array([c*local[0]-s*local[1],s*local[0]+c*local[1],local[2]])+target['position']).tolist()
            half=.13 if target['category']=='pipe' else .19
            with self.subTest(target=target_id),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for name in ('config','semantic','sim'):(root/name).mkdir()
                task={'category':target['category'],'color':target['color'],'instruction':'test','surface_standoff_m':.8}
                (root/'config/task.json').write_text(json.dumps(task))
                (root/'manifest.json').write_text(json.dumps({'scene':'scenes/pool_platform_semantic.usda'}))
                events=[{'event':'initial_observation','detections':[]},
                        {'event':'perception','detections':[{'category':target['category'],'color':target['color'],'surface_world':world([0,half,0])}]}]
                (root/'semantic/events.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
                result={'policy':'qwen','status':'SUCCEEDED','reason':'test','simulation_seconds':2,'frames':2,'llm_calls':1,
                        'path':[[1,*world([0,half+1.,0])],[2,*world([0,half+.8,0])]]}
                (root/'semantic/result.json').write_text(json.dumps(result));(root/'sim/run.json').write_text('{}')
                np.savez(root/'semantic/map.npz',free=np.ones((2,2)),occupied=np.zeros((2,2)),origin=[0,0],res=.1)
                with patch('builtins.print'):audit=analyze(root,root/'analysis')
                self.assertEqual(audit['target']['id'],target_id)
                self.assertAlmostEqual(audit['final_target_surface_distance_xy_m'],.8)
                self.assertAlmostEqual(audit['target_surface_error_median_m'],0.)

if __name__=='__main__':unittest.main()
