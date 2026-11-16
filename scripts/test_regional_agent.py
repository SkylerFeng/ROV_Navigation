import unittest
import numpy as np
from semantic_agent import TaskAgent,load_agent,resolve_region
from semantic_core import ObjectMemory

class RegionalAgentTests(unittest.TestCase):
    def setUp(self):
        self.cfg=resolve_region(load_agent(),'西侧设备区')
        self.target={'category':'box','color':'yellow'}
    def test_expands_then_releases_incorrect_prior(self):
        a=TaskAgent(self.cfg)
        self.assertEqual(a.search_settings(0,[],self.target)['coarse_region_xyxy'],[-6,-2,-3,2.5])
        a.update_phase('SCANNING',[],self.target)
        self.assertEqual(a.phase,'REGION_SEARCH')
        self.assertEqual(a.search_settings(46,[],self.target)['coarse_region_xyxy'],[-7.5,-3.5,-1.5,4.])
        a.search_settings(92,[],self.target)
        self.assertEqual(a.search_settings(138,[],self.target)['coarse_region_xyxy'],[1.,-2.,4.,2.5])
        a.update_phase('READY',[],self.target)
        self.assertEqual(a.phase,'ALTERNATIVE_SEARCH')
        a.search_settings(184,[],self.target)
        self.assertIsNone(a.effective_region)
        a.update_phase('READY',[],self.target)
        self.assertEqual(a.phase,'GLOBAL_SEARCH');self.assertEqual(len(a.search_events),5)
    def test_alternative_transit_does_not_spend_local_search_budget(self):
        a=TaskAgent(self.cfg)
        for t in (0,46,92,138):a.search_settings(t,[],self.target,[-4,0])
        a.search_settings(250,[],self.target,[-4,0])
        self.assertEqual(a.alternative_index,0)
        a.search_settings(260,[],self.target,[2,0])
        a.search_settings(306,[],self.target,[2,0])
        self.assertIsNone(a.effective_region)
    def test_visible_target_overrides_hint_and_pauses_expansion(self):
        a=TaskAgent(self.cfg);a.search_settings(0,[],self.target)
        obj={**self.target,'confirmed':True,'visible_now':True}
        a.search_settings(60,[obj],self.target);a.update_phase('APPROACHING',[obj],self.target)
        a.search_settings(120,[obj],self.target)
        self.assertEqual(a.phase,'APPROACH');self.assertEqual(a.expansion,0)
    def test_region_requires_known_name(self):
        with self.assertRaises(ValueError):resolve_region(self.cfg,'不存在的区域')
    def test_no_prior_is_global(self):
        a=TaskAgent(load_agent());a.search_settings(0,[],self.target);a.search_settings(200,[],self.target)
        a.update_phase('READY',[],self.target)
        self.assertEqual(a.phase,'GLOBAL_SEARCH');self.assertEqual(a.search_events,[])
    def test_position_consistency_and_gap_reset(self):
        m=ObjectMemory(3)
        def d(x):return {**self.target,'surface_world':[x,0,1],'detector_score':.9}
        for i in range(3):m.update([d(i*.01)],i*.2)
        o=m.observe(.5)[0];self.assertTrue(o['confirmed']);self.assertLess(o['position_spread_m'],.02)
        m.update([d(.4)],.6);self.assertGreater(m.observe(.6)[0]['position_spread_m'],.2)
        m.update([d(.4)],3.)
        self.assertFalse(m.observe(3.)[0]['confirmed']);self.assertEqual(m.observe(3.)[0]['position_spread_m'],0)
        self.assertNotIn('position_samples',m.observe(3.)[0])
if __name__=='__main__':unittest.main()
