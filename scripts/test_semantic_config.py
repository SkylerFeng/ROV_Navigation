"""Configuration propagation and rejection checks without ROS/Isaac/API access."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from semantic_config import load_task,load_runtime,load_providers,effective_provider,CONFIG
from semantic_motion import motion_override
from semantic_core import rule_action,validate_action

class ConfigTests(unittest.TestCase):
    def test_check_config_does_not_launch_or_expose_key(self):
        import io
        from contextlib import redirect_stdout
        import run_semantic_trial as trial
        output=io.StringIO()
        with patch('sys.argv',['trial','--policy','qwen','--check-config']), \
             patch.dict(os.environ,{'DASHSCOPE_API_KEY':'test-secret-do-not-print'},clear=True), \
             patch.object(trial.subprocess,'Popen') as launch, redirect_stdout(output):
            trial.main()
        launch.assert_not_called()
        self.assertNotIn('test-secret-do-not-print',output.getvalue())
        self.assertTrue(json.loads(output.getvalue())['credential_present'])

    def temporary_patch(self,value,loader):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'patch.json';p.write_text(json.dumps(value))
            return loader(p)

    def test_partial_patch_preserves_defaults(self):
        value=self.temporary_patch({'scan':{'sweep_deg':180}},load_runtime)
        self.assertEqual(value['scan']['sweep_deg'],180)
        self.assertEqual(value['scan']['timeout_s'],load_runtime()['scan']['timeout_s'])
        self.assertEqual(value['motion']['max_yaw_rate_rad_s'],.25)

    def test_bad_configuration_rejected(self):
        for value in [{'scan':{'sweep_degrees':180}}, {'scan':{'sweep_deg':0}},
                      {'scan':{'sweep_deg':float('nan')}}, {'execution':{'max_llm_calls':1.5}},
                      {'execution':{'tick_s':1}}, {'llm':{'enable_thinking':True}}, {'llm':{'max_consecutive_errors':0}}, {'llm':{'max_consecutive_errors':1.5}}]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.temporary_patch(value,load_runtime)

    def test_fixed_height_and_detector_contract(self):
        for value in [{'depth_m':2},{'category':'person'},{'detector_confidence':1.1},{'confirmation_frames':True}]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.temporary_patch(value,load_task)

    def test_provider_overrides_and_secret_rejection(self):
        providers=self.temporary_patch({'qwen':{'model':'custom-model'}},load_providers)
        with patch.dict(os.environ,{'ROV_LLM_MODEL':'environment-model'}):
            self.assertEqual(effective_provider('qwen',providers)['model'],'environment-model')
        for value in [{'qwen':{'api_key':'should-not-be-here'}}, {'qwen':{'base_url':'https://name:secret@example.com'}}]:
            with self.assertRaises(ValueError):self.temporary_patch(value,load_providers)

    def test_motion_settings_reach_controller(self):
        command={'mode':'scan','stamp':10.,'position':[0,0,1],'yaw':-1.}
        default=motion_override(command,10,[0,0,1],0)
        tuned=motion_override(command,10,[0,0,1],0,settings={'max_yaw_rate_rad_s':.1})
        self.assertEqual(default[1],-.25);self.assertEqual(tuned[1],-.1)

    def test_freshness_shared_by_policy_and_validation(self):
        obs={'task_id':'x','observation_id':1,'target':{'category':'pipe','color':'yellow'},'scan_completed':False,
             'objects':[{'id':'o','category':'pipe','color':'yellow','confirmed':True,'observation_age_s':1.5,
                         'range_m':1.,'approach_candidate_ids':['a']}],
             'candidates':[{'id':'a','kind':'approach','object_id':'o','reachable':True}]}
        action=rule_action(obs);self.assertEqual(action['action'],'approach')
        obs['max_observation_age_s']=1.
        self.assertEqual(rule_action(obs)['action'],'scan')
        with self.assertRaises(ValueError):validate_action(action,obs)

if __name__=='__main__':unittest.main()
