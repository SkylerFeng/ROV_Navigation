"""Regression for blind reverse motion during a ROV trajectory reversal."""
import math
import unittest
from tracking_control import control

class TrackingTests(unittest.TestCase):
    def test_reverse_motion_waits_for_camera_heading(self):
        v, yawrate, status = control([0,0,1],[-1,0,1],[-.2,0,0],0,math.pi)
        self.assertEqual(v,[0.,0.,0.]);self.assertGreater(yawrate,0)
        self.assertEqual(status['mode'],'ALIGNING')
        v, _, status = control([0,0,1],[-1,0,1],[-.2,0,0],math.pi,math.pi)
        self.assertAlmostEqual(v[0],-.3);self.assertEqual(status['mode'],'TRACKING')
    def test_aligning_preserves_depth_regulation(self):
        v,_,_=control([0,0,.9],[-1,0,1],[0,0,0],0,math.pi)
        self.assertEqual(v[:2],[0.,0.]);self.assertGreater(v[2],0)
    def test_speed_and_turn_limits(self):
        for angle in range(-180,181,5):
            v,rate,_=control([0,0,1],[2,2,1],[.3,.3,0],math.radians(angle),0)
            self.assertLessEqual(math.sqrt(sum(x*x for x in v)),.3+1e-9)
            self.assertLessEqual(abs(rate),.5)
    def test_hold_does_not_spin_toward_old_reference_yaw(self):
        v,rate,status=control([0,0,1],[.001,0,1],[0,0,0],1.0,-2.0)
        self.assertEqual(rate,0)
        self.assertEqual(status['mode'],'HOLDING')
    def test_motion_outside_camera_view_waits(self):
        v,_,status=control([0,0,1],[1,1,1],[.1,.1,0],0,0)
        self.assertEqual(v[:2],[0.,0.])
        self.assertEqual(status['mode'],'ALIGNING')
    def test_invalid_reference_holds(self):
        v,rate,s=control([0,0,1],[float('nan'),0,1],[0,0,0],0,0)
        self.assertEqual(v,[0.,0.,0.]);self.assertEqual(rate,0)
    def test_slow_motion_never_uses_opposite_spline_yaw(self):
        # Actual failure: a slow NW command was approved using a SE spline yaw.
        v,rate,s=control([0,0,1],[0,0,1],[-.015,.008,0],-1.3,-1.3)
        self.assertEqual(v[:2],[0.,0.])
        self.assertEqual(s['mode'],'ALIGNING')
        self.assertAlmostEqual(s['target_yaw'],math.atan2(.008,-.015))
    def test_small_inertial_overshoot_keeps_reference_direction(self):
        v,rate,s=control([.025,0,1],[0,0,1],[.03,0,0],0,0)
        self.assertEqual(s['mode'],'TRACKING')
        self.assertGreater(v[0],0)
        self.assertAlmostEqual(rate,0)
    def test_every_nontrivial_command_is_inside_heading_limit(self):
        for speed in [.0001,.005,.009,.011,.019,.021,.1,.3]:
            for angle in range(-180,180,10):
                yaw=math.radians(angle)
                v,_,s=control([0,0,1],[.04,0,1],[-speed,speed,0],yaw,yaw)
                if math.hypot(*v[:2])>1e-6:
                    error=math.atan2(math.sin(math.atan2(v[1],v[0])-yaw),math.cos(math.atan2(v[1],v[0])-yaw))
                    self.assertLess(abs(error),math.radians(20)+1e-9)

if __name__=='__main__':unittest.main()
