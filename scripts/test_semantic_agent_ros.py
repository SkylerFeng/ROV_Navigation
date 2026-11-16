"""Exercise the integrated tick wrapper with recorded-state fixtures, no ROS graph."""
import unittest
from types import MethodType
import test_semantic_recovery_ros as recovery_tests
from semantic_navigation import SemanticNavigation
from semantic_agent import TaskAgent,load_agent
from semantic_core import ExplorationGrid
import numpy as np

class AgentIntegrationTests(unittest.TestCase):
    def fixture(self):
        n=recovery_tests.RecoveryStateTests().fixture();n.agent=TaskAgent(load_agent())
        n.agent_complete=MethodType(SemanticNavigation.agent_complete,n)
        n.planner_state='RUNNING';n.scan_accum=0.;n.previous_yaw=0.;n.scan_direction=-1.
        n.scans_at_viewpoint=0;n.next_scan_center=None
        return n
    def test_scan_completion_is_in_next_observation_memory(self):
        n=self.fixture();n.mode='SCANNING';n.action_started=0.;n.time=40.;n.grid=type('Grid',(),{'mark_scanned':lambda *_:None})()
        n.agent.start({'action':'scan'},{'observation_id':1,'candidates':[]},0)
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY');self.assertIsNone(n.agent.current)
        self.assertEqual(n.agent.summary()['recent_results'][0]['status'],'TIMEOUT')
        self.assertEqual(n.events[-1]['event'] if isinstance(n.events[-1],dict) else n.events[-1][0],'agent_tool_result')
    def test_approach_arrival_waits_for_verification(self):
        n=self.fixture();n.mode='APPROACHING';n.action_started=9.
        n.active={'position':[0,0,1],'yaw':0,'progress_distance':0,'progress_time':10,'object_id':'target'}
        n.agent.start({'action':'approach'},{'observation_id':1,'candidates':[]},9.)
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'VERIFYING');self.assertIsNotNone(n.agent.current)
    def test_spin_safely_holds_and_records_failed_tool(self):
        n=self.fixture();n.mode='EXPLORING';n.action_started=0;n.time=21.
        c={'id':'vp','position':[1,0,1],'kind':'explore'}
        n.agent.start({'action':'explore','candidate_id':'vp'},{'observation_id':1,'candidates':[c]},0)
        for i in range(21):n.agent.loop(i,[0,0,1],i*.25,'EXPLORING')
        import math
        n.odom.pose.pose.orientation.w=math.cos(5.25/2);n.odom.pose.pose.orientation.z=math.sin(5.25/2)
        n.active={'position':[1,0,1]};n.scan_completed=False
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY');self.assertEqual(n.last_result,'rotation_without_translation_choose_another_viewpoint')
        self.assertEqual(n.agent.summary()['recent_results'][-1]['status'],'FAILED')
    def test_stable_target_shift_requests_safe_replan(self):
        n=self.fixture();n.mode='APPROACHING';n.time=20.;n.action_started=0.
        n.active={'position':[2,0,1],'yaw':0,'progress_distance':2,'progress_time':20,
                  'object_id':'target','issued_at':0,'target_surface_at_issue':[3,0,1]}
        obj={'id':'target','category':n.cfg['category'],'color':n.cfg['color'],
             'confirmed':True,'visible_now':True,'surface_world':[3.5,0,1],'position_spread_m':.02}
        n.memory.observe=lambda t:[obj]
        n.agent.start({'action':'approach'},{'observation_id':1,'candidates':[]},0)
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY');self.assertEqual(n.last_result,'target_position_updated')
        self.assertEqual(n.agent.history[-1]['status'],'ABORTED')
    def test_unstable_target_does_not_trigger_replan(self):
        n=self.fixture();n.mode='APPROACHING';n.time=20.;n.action_started=0.
        n.active={'position':[2,0,1],'yaw':0,'progress_distance':2,'progress_time':20,
                  'object_id':'target','issued_at':0,'target_surface_at_issue':[3,0,1]}
        n.memory.observe=lambda t:[{'id':'target','category':n.cfg['category'],'color':n.cfg['color'],
             'confirmed':True,'visible_now':True,'surface_world':[3.5,0,1],'position_spread_m':.3}]
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'APPROACHING')
    def test_conflicting_category_aborts_active_approach(self):
        n=self.fixture();n.mode='APPROACHING';n.time=20.;n.action_started=0.
        n.active={'position':[2,0,1],'yaw':0,'progress_distance':2,'progress_time':20,'object_id':'target'}
        n.memory.observe=lambda t:[{'id':'target','category':n.cfg['category'],'color':n.cfg['color'],
             'confirmed':False,'category_conflict':True,'visible_now':True}]
        n.agent.start({'action':'approach'},{'observation_id':1,'candidates':[]},0)
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY');self.assertEqual(n.last_result,'category_conflict_reobserve')
        self.assertIsNone(n.target_anchor);n.lease.assert_called_with('hold')
        self.assertEqual(n.agent.history[-1]['status'],'ABORTED')
    def test_hint_keeps_unknown_cells_out_of_candidates(self):
        grid=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],.15,.25,inspection_range=2.5)
        grid.free[:]=grid.inside
        for ix in range(grid.shape[0]):
            for iy in range(grid.shape[1]):
                if grid.xy((ix,iy))[0]>1:grid.free[ix,iy]=False
        candidates=grid.candidates([0,0,1],[],settings={'coarse_region_xyxy':[1,-2,3,2],'region_weight':2})
        self.assertTrue(candidates)
        for c in candidates:self.assertTrue(grid.safe()[grid.cell(c['position'])])
if __name__=='__main__':unittest.main()
