import math
import unittest
from semantic_recovery import matching_target, recovery_heading
from tracking_control import smooth_yaw_rate
from semantic_config import load_runtime

class RecoveryTests(unittest.TestCase):
    def test_memory_is_not_fresh_evidence(self):
        obj={'id':'a','confirmed':True,'category':'pipe','color':'yellow',
             'last_seen':1.,'surface_world':[0,0,1]}
        target={'category':'pipe','color':'yellow'}
        self.assertIsNone(matching_target([obj],target,5,2))
        self.assertIs(matching_target([obj],target,2,2),obj)
        self.assertIsNone(matching_target([obj],target,2,2,[4,0,1],.7))
        obj['confirmed']=False
        self.assertIsNone(matching_target([obj],target,2,2))

    def test_recovery_cannot_turn_full_circle(self):
        settings=load_runtime()['recovery']
        for i in range(201):
            angle=recovery_heading([0,0,1],[1,0,1],i*.1,settings)
            self.assertLessEqual(abs(angle),math.radians(settings['sweep_deg'])+1e-9)
        self.assertEqual(recovery_heading([0,0,1],[1,0,1],1,settings),0)

    def test_yaw_slew_bounds_and_clock_reset(self):
        previous=.2
        for _ in range(20):
            new=smooth_yaw_rate(previous,-.3,.1,.4)
            self.assertLessEqual(abs(new-previous),.04000001)
            previous=new
        self.assertAlmostEqual(previous,-.3)
        self.assertEqual(smooth_yaw_rate(.3,-.3,-1,.4),0)

if __name__=='__main__':unittest.main()
