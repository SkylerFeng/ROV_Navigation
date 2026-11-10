import unittest
from semantic_instruction import validate_resolution,apply_resolution

class InstructionTests(unittest.TestCase):
    def test_valid_task_changes_target_and_distance(self):
        record={'instruction':'approach blue tube','resolution':{'status':'accepted','category':'pipe','color':'blue','surface_standoff_m':1.,'reason':'explicit'}}
        task=apply_resolution({'color':'yellow','category':'box','depth_m':1.,'surface_standoff_m':.8},record)
        self.assertEqual((task['category'],task['color'],task['surface_standoff_m']),('pipe','blue',1.))
        self.assertEqual(task['depth_m'],1.)
    def test_rejected_task_cannot_start(self):
        for status in ('clarify','unsupported'):
            record={'instruction':'ambiguous','resolution':{'status':status,'category':None,'color':None,'surface_standoff_m':None,'reason':'needs context'}}
            self.assertEqual(validate_resolution(record['resolution'])['status'],status)
            with self.assertRaises(ValueError):apply_resolution({},record)
    def test_invalid_fields_and_distances(self):
        base={'status':'accepted','category':'pipe','color':'blue','surface_standoff_m':None,'reason':'ok'}
        for patch in ({'color':'green'},{'surface_standoff_m':True},{'surface_standoff_m':float('nan')},
                      {'surface_standoff_m':0.1},{'extra':'not allowed'}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):validate_resolution({**base,**patch})
    def test_unspecified_distance_preserves_configuration(self):
        record={'instruction':'blue pipe','resolution':{'status':'accepted','category':'pipe','color':'blue','surface_standoff_m':None,'reason':''}}
        self.assertEqual(apply_resolution({'surface_standoff_m':.9},record)['surface_standoff_m'],.9)

    def test_launcher_rejected_instruction_starts_no_process(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        import run_semantic_trial as trial
        record={'instruction':'go to pipe','resolution':{'status':'clarify','category':None,'color':None,'surface_standoff_m':None,'reason':'specify color'}}
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            with patch('sys.argv',['trial','--policy','qwen','--instruction','go to pipe','--output',str(output)]), \
                 patch.dict('os.environ',{'DASHSCOPE_API_KEY':'local-test'}), \
                 patch('semantic_credentials.load_credentials'), \
                 patch('semantic_instruction.resolve_instruction',return_value=record), \
                 patch.object(trial.subprocess,'Popen') as launch,patch('builtins.print'):
                trial.main()
            launch.assert_not_called()
            self.assertEqual(json.loads((output/'summary.json').read_text())['stop_reason'],'instruction_clarify')
            self.assertFalse((output/'config').exists())

if __name__=='__main__':unittest.main()
