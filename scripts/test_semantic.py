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
    def test_selected_frontier_survives_reranking_but_not_obstacles(self):
        grid=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        grid.free[:]=grid.inside
        candidate={'id':'frontier','kind':'explore','position':[1,0,1],'reachable':True}
        pending={'candidates':[candidate]};current={'candidates':[]}
        action={'action':'explore','candidate_id':'frontier'}
        self.assertTrue(refresh_selected_explore(action,pending,current,grid,[0,0,1]))
        self.assertEqual(current['candidates'][0]['position'],[1,0,1])
        grid.occupied[grid.cell([1,0])]=True;grid._safe=None
        self.assertFalse(refresh_selected_explore(action,pending,{'candidates':[]},grid,[0,0,1]))
        self.assertFalse(refresh_selected_explore({'action':'explore','candidate_id':'invented'},pending,{'candidates':[]},grid,[0,0,1]))
    def test_escape_inflation_uses_observed_monotonic_clearance(self):
        grid=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        grid.free[:]=grid.inside;grid.occupied[grid.cell([0,0])]=True
        start=[.35,0,1];self.assertFalse(grid.safe()[grid.cell(start)])
        costs,parent=grid.reachable(start)
        self.assertIn(grid.cell([1,0]),costs)
        self.assertTrue(all(grid.safe()[c] for c in costs))
        self.assertNotIn(grid.cell([0,0]),parent)
        # No escape from an occupied start, nor across unobserved space.
        self.assertFalse(grid.reachable([0,0,1])[0])
        grid.free[:]=False;grid.free[grid.cell(start)]=True;grid._safe=None
        self.assertFalse(grid.reachable(start)[0])
    def test_failed_approach_position_is_not_reselected(self):
        grid=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        grid.free[:]=grid.inside
        obj={'id':'target','confirmed':True,'observation_age_s':0,'surface_world':[0,0,1]}
        first=next(c for c in grid.candidates([1.5,0,1],[obj]) if c['kind']=='approach')
        second=next(c for c in grid.candidates([1.5,0,1],[obj],excluded_approaches=[first['position']]) if c['kind']=='approach')
        self.assertGreaterEqual(math.dist(first['position'],second['position']),.45)
        self.assertGreater(second['position'][0],0)
    def test_report_cannot_abandon_unfinished_search(self):
        obs=self.observation()
        action={'task_id':'test','observation_id':1,'action':'report','reason_code':'target not seen'}
        with self.assertRaisesRegex(ValueError,'premature report'):validate_action(action,obs)
        obs['scan_completed']=True
        obs['candidates']=[{'id':'frontier','kind':'explore','reachable':True}]
        with self.assertRaisesRegex(ValueError,'premature report'):validate_action(action,obs)
        action.update(action='explore',candidate_id='frontier')
        self.assertEqual(validate_action(action,obs)['action'],'explore')
    def test_report_allowed_after_search_exhausted(self):
        obs=self.observation();obs['scan_completed']=True
        action={'task_id':'test','observation_id':1,'action':'report','reason_code':'no reachable frontier'}
        self.assertEqual(validate_action(action,obs)['action'],'report')
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
    def test_thin_obstacle_between_free_space_rays_is_retained(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        depth=np.zeros((16,16));depth[4,4]=1.
        g.update(depth,[[100,0,4],[0,100,4],[0,0,1]],[0,0,1.1],[.5,-.5,.5,-.5],[0,0,1])
        self.assertTrue(g.occupied.any())
        occupied=np.array([g.xy(c) for c in np.argwhere(g.occupied)])
        self.assertLess(np.linalg.norm(occupied-[1,0],axis=1).min(),.2)

    def test_geometrically_free_space_can_still_need_visual_inspection(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],inspection_range=2.5)
        g.free[:]=g.inside
        self.assertTrue(g.candidates([0,0,1],[]))
        g.inspected[:]=True
        self.assertEqual(g.candidates([0,0,1],[]),[])

    def test_open_area_search_keeps_nearby_viewpoints(self):
        g=ExplorationGrid([[-6,-3],[6,-3],[6,3],[-6,3]],inspection_range=2.5)
        g.free[:]=g.inside;g.mark_scanned([0,0,1])
        candidates=g.candidates([0,0,1],[])
        self.assertTrue(candidates)
        self.assertLess(candidates[0]['path_length_m'],1.5)

    def test_inspection_uses_actual_rays_and_bounded_range(self):
        g=ExplorationGrid([[-4,-4],[4,-4],[4,4],[-4,4]],inspection_range=1.5)
        q=[.5,-.5,.5,-.5]
        g.update(np.array([[3.]]),np.eye(3),[0,0,1.1],q,[0,0,1])
        self.assertTrue(g.inspected[g.cell([1,0])])
        self.assertTrue(g.free[g.cell([2,0])])
        self.assertFalse(g.inspected[g.cell([2,0])])
        self.assertFalse(g.inspected[g.cell([-1,0])])

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

    def test_failed_exploration_excludes_nearby_goals(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        cells=np.indices(g.shape).reshape(2,-1).T
        xy=g.origin+(cells+.5)*g.res
        g.free[:]=(g.inside.ravel() & (xy[:,0]<1)).reshape(g.shape)
        candidates=g.candidates([0,0,1],[])
        self.assertTrue(candidates)
        failed=candidates[0]['position']
        alternatives=g.candidates([0,0,1],[],excluded_explores=[failed])
        self.assertTrue(alternatives)
        self.assertTrue(all(math.dist(c['position'][:2],failed[:2])>=.6 for c in alternatives))

    def test_small_unknown_gap_does_not_hide_larger_information_region(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        g.free[:]=g.inside
        root=g.cell([0,0]);gap=(root[0]+2,root[1]);far=(root[0]+5,root[1])
        g.free[gap]=False;g.free[far]=False
        meaningful=np.zeros(g.shape,bool);meaningful[far]=True
        self.assertGreater(g.visible_unknown_gain(root,meaningful),0)
        g.occupied[gap]=True
        self.assertEqual(g.visible_unknown_gain(root,meaningful),0)

    def test_exploration_scan_heading_faces_information(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]])
        g.free[:]=g.inside;meaningful=np.zeros(g.shape,bool)
        meaningful[g.cell([1.5,0])]=True
        gain,heading=g.visible_unknown_gain(g.cell([0,0]),meaningful,with_heading=True)
        self.assertGreater(gain,0);self.assertLess(abs(heading),.2)
