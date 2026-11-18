import unittest
import numpy as np
from semantic_agent import TaskAgent,load_agent,resolve_region
from semantic_core import ExplorationGrid

class EvidenceSearch(unittest.TestCase):
    def setUp(self):
        self.g=ExplorationGrid([[-7,-3],[6,-3],[6,3],[-7,3]],.15,.4,inspection_range=2.5)
        self.g.free[:]=self.g.inside
        self.a=TaskAgent(resolve_region(load_agent(),'西侧设备区'))
        self.target={'color':'yellow','category':'box'}
    def test_travel_time_cannot_abandon_unobserved_prior(self):
        for t in (0,100,300):self.a.search_settings(t,[],self.target,[2,0],self.g)
        self.assertEqual(self.a.effective_region,[-6,-2,-3,2.5])
        self.assertEqual(self.a.search_events,[])
    def test_close_coverage_and_distinct_views_release_wrong_hint(self):
        self.g.inspected[:]=self.g.inside
        self.a.search_settings(0,[],self.target,[-4,0],self.g)
        self.assertEqual(self.a.search_events,[])
        self.g.scan_positions=[np.array([-4,0]),np.array([-4,1.])]
        self.a.search_settings(50,[],self.target,[-4,1],self.g)
        self.assertEqual(self.a.effective_region,[1.,-2.,4.,2.5])
        self.assertEqual(len(self.a.search_events),1)
    def test_matching_visual_target_prevents_region_release(self):
        self.g.inspected[:]=self.g.inside
        self.g.scan_positions=[np.array([-4,0]),np.array([-4,1.])]
        self.a.search_settings(50,[dict(self.target,confirmed=True,visible_now=True)],self.target,[-4,1],self.g)
        self.assertEqual(self.a.search_events,[])
    def partial_coverage(self):
        self.g.inspected[:]=self.g.inside
        self.g.inspected[self.g.cell([-5.5,0])]=False
        self.g.scan_positions=[np.array([-4,0]),np.array([-4,1.])]
    def test_coverage_alone_does_not_abandon_occluded_region(self):
        self.partial_coverage()
        self.a.search_settings(50,[],self.target,[-4,1],self.g)
        self.assertEqual(self.a.search_events,[])
    def test_useful_reachable_view_prevents_region_release(self):
        self.partial_coverage()
        views=[{'kind':'explore','information_gain_score':20}]
        self.a.search_settings(50,[],self.target,[-4,1],self.g,candidates=views)
        self.assertEqual(self.a.search_events,[])
        self.assertEqual(self.a.region_evidence['productive_viewpoints'],1)
    def test_exhausted_filtered_views_release_wrong_hint(self):
        self.partial_coverage()
        self.a.search_settings(50,[],self.target,[-4,1],self.g,candidates=[])
        self.assertEqual(len(self.a.search_events),1)
        self.assertEqual(self.a.search_events[0]['reason'],'regional_viewpoints_exhausted')
    def test_transfer_is_not_new_observation_evidence(self):
        self.partial_coverage()
        self.a.search_settings(50,[],self.target,[-4,1],self.g,
            candidates=[{'kind':'explore','information_gain_score':0,'purpose':'transit'}])
        self.assertEqual(len(self.a.search_events),1)
    def test_insignificant_residual_gain_does_not_lock_region(self):
        self.partial_coverage()
        self.a.search_settings(50,[],self.target,[-4,1],self.g,
            candidates=[{'kind':'explore','information_gain_score':1}])
        self.assertEqual(len(self.a.search_events),1)
    def test_large_opposite_unknown_room_does_not_outscore_region(self):
        cs=self.g.candidates([-2,0,1],[],settings={'coarse_region_xyxy':[-6,-2,-3,2.5],'regional_information':True})
        self.assertTrue(cs)
        best=max(cs,key=lambda c:c['score'])
        self.assertLess(best['position'][0],-2)
        self.assertLess(np.cos(best['inspection_yaw']),0)

if __name__=='__main__':unittest.main()
