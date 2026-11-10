import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from navigation_config import load_navigation, planner_parameters
from experiment import load_experiment
from tracking_control import control

class NavigationConfigTests(unittest.TestCase):
    def test_defaults_preserve_controller(self):
        args=([0,0,1],[1,.2,1],[.1,0,0],0,0)
        self.assertEqual(control(*args),control(*args,settings=load_navigation()['tracker']))

    def test_profile_and_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'nav.json'
            p.write_text(json.dumps({'limits':{'max_velocity':.17},'planner':{'planning_horizon_m':2.1}}))
            with patch.dict(os.environ,{'ROV_NAVIGATION_CONFIG':str(p),'ROV_EXPERIMENT_OVERRIDES':''}):
                config=load_experiment('platform_semantic')
            self.assertEqual(config['max_velocity'],.17)
            params=planner_parameters(config['navigation'])
            self.assertEqual(params['fsm/planning_horizon'],2.1)
            self.assertEqual(params['manager/planning_horizon'],2.1)
            snapshot=Path(tmp)/'snapshot.json'
            snapshot.write_text(json.dumps({k:v for k,v in config.items() if k not in ('scenario','scene_file','overrides_file')}))
            with patch.dict(os.environ,{'ROV_NAVIGATION_CONFIG':'','ROV_EXPERIMENT_OVERRIDES':str(snapshot)}):
                restored=load_experiment('platform_semantic')
            self.assertEqual(restored['navigation'],config['navigation'])
            self.assertEqual(restored['max_velocity'],.17)

    def test_bad_parameters_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'nav.json'
            for value in ({'typo':{}},{'tracker':{'yaw_kpp':1}},
                          {'limits':{'max_velocity':-1}},{'limits':{'align_before_translation':1}},
                          {'planner':{'map_resolution_m':float('nan')}},
                          {'tracker':{'input_timeout_s':.001}},
                          {'limits':{'max_heading_error_deg':100}}):
                with self.subTest(value=value):
                    p.write_text(json.dumps(value))
                    with self.assertRaises(ValueError):load_navigation(p)

    def test_tracker_tuning_changes_output(self):
        settings={'position_kp':.1,'depth_kp':.2,'yaw_kp':.3,'max_yaw_rate_rad_s':.07}
        v,rate,_=control([0,0,.9],[1,0,1],[0,0,0],0,1,align=False,settings=settings)
        self.assertAlmostEqual(v[0],.1)
        self.assertAlmostEqual(v[2],.02)
        self.assertAlmostEqual(rate,.07)

if __name__=='__main__':unittest.main()
