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
    def test_final_alignment_does_not_consume_visual_verification_budget(self):
        from types import SimpleNamespace as NS
        import math
        n=self.fixture();n.mode='VERIFYING';n.time=25.;n.action_started=0.
        n.active={'object_id':'target','position':[0,0,1]};n.hold_yaw=math.pi
        n.verification_aligned_at=None;n.verified_since=None;n.last_verify_log=n.time
        n.odom.twist=NS(twist=NS(linear=NS(x=0.,y=0.,z=0.)))
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'VERIFYING');n.finish.assert_not_called()
        n.time=76.;n.last_verify_log=n.time
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY')
    def test_entry_alignment_rechecks_new_obstacles(self):
        from unittest.mock import Mock
        n=self.fixture();n.mode='NAV_ALIGN';n.action_started=9.;n.hold_yaw=0.
        n.active={'position':[1,0,1]};n.aligned_navigation_mode='EXPLORING'
        n.publish_navigation_goal=Mock()
        n.grid=type('Grid',(),{'reachable':lambda *_:({},{}),'cell':lambda *_:(1,0)})()
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'READY');n.publish_navigation_goal.assert_not_called()
    def test_entry_alignment_releases_only_after_facing_path(self):
        from unittest.mock import Mock
        import math
        n=self.fixture();n.mode='NAV_ALIGN';n.action_started=9.;n.hold_yaw=math.pi/2;n.anchor=[0,0,1]
        n.active={'position':[1,0,1]};n.aligned_navigation_mode='EXPLORING'
        n.publish_navigation_goal=Mock()
        n.grid=type('Grid',(),{'reachable':lambda *_:({(1,0):1},{}),'cell':lambda *_:(1,0)})()
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'NAV_ALIGN');n.publish_navigation_goal.assert_not_called()
        n.hold_yaw=0.
        recovery_tests.RecoveryStateTests().tick(n)
        self.assertEqual(n.mode,'EXPLORING');n.publish_navigation_goal.assert_called_once_with([1,0,1])
    def test_stalled_alignment_stops_instead_of_retrying_same_target(self):
        import math
        n=self.fixture();n.mode='NAV_ALIGN';n.action_started=0.;n.time=20.;n.anchor=[0,0,1]
        n.hold_yaw=1.;n.alignment_best_error=1.;n.alignment_progress_time=0.
        n.grid=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],.1,.4)
        n.grid.free[:]=n.grid.inside
        n.active={'position':[1,0,1]}
        recovery_tests.RecoveryStateTests().tick(n)
        n.finish.assert_called_once_with('FAILED','alignment_without_progress_no_certified_escape')
        self.assertEqual(n.hold_yaw,0.)
        n.lease.assert_called_with('hold')
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
    def test_observation_preserves_hint_with_productive_filtered_view(self):
        from semantic_agent import resolve_region
        from unittest.mock import Mock
        from types import SimpleNamespace as NS
        n=self.fixture();n.sequence=0;n.task_id='test';n.scan_completed=True
        n.grid=ExplorationGrid([[-7,-3],[6,-3],[6,3],[-7,3]],.15,.4,inspection_range=2.5)
        n.grid.free[:]=n.grid.inside;n.grid.inspected[:]=n.grid.inside
        n.grid.inspected[n.grid.cell([-5.5,0])]=False
        n.grid.scan_positions=[np.array([-4.,0]),np.array([-4.,1])]
        n.agent=TaskAgent(resolve_region(load_agent(),'西侧设备区'))
        c={'id':'vp','kind':'explore','position':[-5,0,1],'score':1.,'information_gain_score':30}
        n.grid.candidates=Mock(return_value=[c])
        obs=SemanticNavigation.observation(n,[-4,1,1])
        self.assertEqual(obs['candidates'][0]['id'],'vp')
        self.assertEqual(n.agent.effective_region,[-6,-2,-3,2.5])
        n.grid.candidates.assert_called_once()
        n.grid.candidates=Mock(side_effect=[[],[dict(c,id='east')]])
        obs=SemanticNavigation.observation(n,[-4,1,1])
        self.assertEqual(n.agent.effective_region,[1,-2,4,2.5])
        self.assertEqual(obs['candidates'][0]['id'],'east')
        self.assertEqual(n.grid.candidates.call_count,2)
if __name__=='__main__':unittest.main()
