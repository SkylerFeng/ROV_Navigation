import unittest,json,math,os
import numpy as np
from semantic_core import *
from semantic_motion import motion_override,parse_motion
class SemanticTests(unittest.TestCase):
    def observation(self):
        return {'task_id':'test','observation_id':1,'target':{'category':'pipe','color':'yellow'},'scan_completed':False,'objects':[], 'candidates':[]}
    def test_range_not_z(self):
        pts,_=range_points(np.array([[2.]]),[[1,0,-1],[0,1,0],[0,0,1]],[0,0,0],[1,0,0,0])
        np.testing.assert_allclose(pts,[[math.sqrt(2),0,math.sqrt(2)]])
    def test_world_rotation(self):
        pts,_=range_points(np.array([[2.]]),np.eye(3),[1,2,3],[math.sqrt(.5),0,math.sqrt(.5),0])
        np.testing.assert_allclose(pts,[[3,2,3]],atol=1e-8)
    def test_invalid_range(self):
        pts,_=range_points(np.array([[0.,np.nan,9.]]),np.eye(3),[0,0,0],[1,0,0,0]);self.assertEqual(len(pts),0)
    def test_foreground_localization(self):
        rgb=np.zeros((20,20,3),np.uint8);rgb[5:15,5:15]=[255,210,0]
        d=np.full((20,20),5.);d[5:15,5:15]=2.
        o=localize_detection(rgb,d,[[100,0,10],[0,100,10],[0,0,1]],[0,0,0],[1,0,0,0],[0,0,20,20])
        self.assertEqual(o['color'],'yellow');self.assertAlmostEqual(o['range_m'],2.);self.assertLess(abs(o['surface_world'][2]-2),.01)
    def test_memory_requires_frames(self):
        m=ObjectMemory();d={'category':'pipe','color':'yellow','surface_world':[0,0,1],'detector_score':.9}
        m.update([d],0);m.update([d],.2);self.assertFalse(m.observe(.2)[0]['confirmed'])
        m.update([d],.4);self.assertTrue(m.observe(.4)[0]['confirmed']);self.assertFalse(m.observe(2)[0]['visible_now'])
    def test_rule_scans(self):self.assertEqual(rule_action(self.observation())['action'],'scan')
    def test_wrong_target_rejected(self):
        o=self.observation();o['objects']=[{'id':'o','category':'box','color':'yellow','confirmed':True,'observation_age_s':0}]
        o['candidates']=[{'id':'c','kind':'approach','reachable':True,'object_id':'o'}]
        with self.assertRaises(ValueError):validate_action({'task_id':'test','observation_id':1,'action':'approach','object_id':'o','candidate_id':'c','reason_code':'x'},o)
    def test_stale_action_rejected(self):
        o=self.observation();a=rule_action(o);a['observation_id']=0
        with self.assertRaises(ValueError):validate_action(a,o)
    def test_invented_coordinate_rejected(self):
        o=self.observation();a=rule_action(o);a['position']=[1,2,3]
        with self.assertRaises(ValueError):validate_action(a,o)
    def test_unknown_grid_not_free(self):
        g=ExplorationGrid([[-2,-2],[2,-2],[2,2],[-2,2]])
        self.assertFalse(g.safe().any());self.assertFalse(g.reachable([0,0])[0])
    def test_occupied_inflation(self):
        g=ExplorationGrid([[-2,-2],[2,-2],[2,2],[-2,2]]);g.free[:]=g.inside;g.occupied[g.cell([0,0])]=True
        self.assertFalse(g.safe()[g.cell([.3,0])]);self.assertTrue(g.safe()[g.cell([1,0])])
    def test_lease_expires(self):
        self.assertEqual(motion_override({'stamp':0,'mode':'navigate'},1,[0,0,1],0)[2],'SEMANTIC_STALE')
        self.assertIsNone(motion_override({'stamp':1,'mode':'navigate'},1,[0,0,1],0))
    def test_invalid_lease(self):
        with self.assertRaises(ValueError):parse_motion(json.dumps({'mode':'fly','position':[0,0,1],'yaw':0,'stamp':0}))
if __name__=='__main__':unittest.main()

class GridRegressionTests(unittest.TestCase):
    def test_floor_ray_clears_segment_without_occupied_floor(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        # Optical Z becomes world +X and optical Y becomes world -Z.
        q=[.5,-.5,.5,-.5]
        d=np.full((1,1),2.)
        g.update(d,[[10,0,0],[0,10,-2],[0,0,1]],[0,0,1.1],q,[0,0,1])
        self.assertTrue(g.free.any())
        self.assertTrue(g.free[g.cell([.6,0])])
    def test_unknown_gain_respects_occlusion(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        g.free[:]=g.inside
        center=g.cell([0,0]);g.free[center]=False
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
            g.occupied[center[0]+dx,center[1]+dy]=True
        meaningful=np.zeros(g.shape,bool);meaningful[center]=True
        self.assertEqual(g.visible_unknown_gain(g.cell([-1.5,0]),meaningful),0)
