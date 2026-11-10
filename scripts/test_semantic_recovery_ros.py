"""Actual state-machine methods with recorded-style inputs; no ROS graph/API/Isaac.
Run after sourcing /opt/ros/humble/setup.bash and adding scripts to PYTHONPATH.
"""
import unittest
from types import SimpleNamespace as NS, MethodType
from concurrent.futures import Future
from unittest.mock import Mock
from semantic_navigation import SemanticNavigation
from semantic_config import load_runtime,load_task

class RecoveryStateTests(unittest.TestCase):
    def fixture(self):
        n=NS(time=10.,runtime=load_runtime(),cfg=load_task(),target_anchor=[1,0,1],
             target_seen=9.,recovery_attempts=0,cooldown_until=-100.,mode='READY',
             anchor=None,hold_yaw=0.,started=1.,last_sensor=10.,last_frame_wall=0.,
             grid=None,planner_ready=True,last_result='',llm_errors=0,failed_approaches=[],failed_explores=[],
             frames=0,memory=NS(observe=lambda t:[],objects={}),status=NS(publish=Mock()))
        n.now=lambda:n.time
        n.odom=NS(header=NS(stamp=NS(sec=10,nanosec=0)),
                  pose=NS(pose=NS(position=NS(x=0,y=0,z=1),orientation=NS(w=1,x=0,y=0,z=0))))
        n.events=[];n.record=lambda event,data:n.events.append((event,data))
        n.perceive=Mock();n.lease=Mock();n.finish=Mock();n.decide=Mock()
        for name in ('hold','begin_recovery','remember_target','tick'):
            setattr(n,name,MethodType(getattr(SemanticNavigation,name),n))
        n.observation=lambda p:{'objects':[],'candidates':[],'task_id':'test','observation_id':1}
        return n

    def tick(self,n):
        import time
        n.last_sensor=n.time;n.last_frame_wall=time.monotonic()
        n.odom.header.stamp.sec=int(n.time)
        n.tick()

    def test_expired_approach_enters_recovery_not_remote_exploration(self):
        n=self.fixture();n.mode='DECIDING'
        n.pending_observation={'observation_id':1}
        action={'task_id':'test','observation_id':1,'action':'approach',
                'candidate_id':'approach_obj','object_id':'obj','reason_code':'target_visible'}
        n.future=Future();n.future.set_result((action,{}))
        self.tick(n)
        self.assertEqual(n.mode,'RECOVERING');n.decide.assert_not_called()
        self.assertEqual(n.recovery_attempts,1)

    def test_recovery_is_bounded_and_does_not_complete_from_memory(self):
        n=self.fixture();self.assertTrue(n.begin_recovery([0,0,1],0,'lost'))
        self.tick(n);self.assertEqual(n.mode,'RECOVERING');n.decide.assert_not_called();n.finish.assert_not_called()
        n.time+=n.runtime['recovery']['timeout_s']+.1;self.tick(n)
        self.assertEqual(n.mode,'READY');self.assertGreater(n.cooldown_until,n.time)
        self.assertIsNone(n.target_anchor);n.finish.assert_not_called()

    def test_fresh_reacquisition_returns_to_llm_without_executing_goal(self):
        n=self.fixture();n.begin_recovery([0,0,1],0,'lost')
        obj={'id':'new_track','confirmed':True,'category':'pipe','color':'yellow',
             'last_seen':10.,'surface_world':[1,0,1]}
        n.observation=lambda p:{'objects':[obj],'candidates':[{'kind':'approach','object_id':'new_track'}]}
        self.tick(n)
        self.assertEqual(n.mode,'READY');self.assertEqual(n.last_result,'target_reacquired_locally')
        n.finish.assert_not_called();n.decide.assert_not_called()

    def test_attempt_budget_is_enforced(self):
        n=self.fixture();n.recovery_attempts=n.runtime['recovery']['max_attempts']
        self.assertFalse(n.begin_recovery([0,0,1],0,'lost'))
        self.assertGreater(n.cooldown_until,n.time)

    def test_no_progress_releases_exploration_without_false_success(self):
        n=self.fixture();n.time=50.;n.mode='EXPLORING';n.planner_state='EXEC_TRAJ';n.action_started=10.
        n.active={'position':[2,0,1],'progress_time':10.,'progress_distance':2.}
        self.tick(n)
        self.assertEqual(n.mode,'READY');n.finish.assert_not_called()
        self.assertEqual(n.last_result,'no_progress_choose_another_viewpoint')
        self.assertEqual(n.failed_explores,[[2,0,1]])
        self.assertTrue(any(event=='navigation_no_progress' for event,_ in n.events))

    def test_progress_updates_deadline(self):
        n=self.fixture();n.time=50.;n.mode='EXPLORING';n.planner_state='EXEC_TRAJ';n.action_started=10.
        n.active={'position':[2,0,1],'progress_time':10.,'progress_distance':3.}
        self.tick(n)
        self.assertEqual(n.mode,'EXPLORING');self.assertEqual(n.active['progress_time'],50.)

    def test_blocked_exploration_is_excluded_on_next_decision(self):
        n=self.fixture();n.time=50.;n.mode='EXPLORING';n.planner_state='BLOCKED_GOAL';n.action_started=40.
        n.active={'position':[2,0,1],'progress_time':40.,'progress_distance':2.}
        self.tick(n)
        self.assertEqual(n.mode,'READY');self.assertEqual(n.failed_explores,[[2,0,1]])
        n.finish.assert_not_called()

    def test_frontier_exhaustion_requests_bounded_extra_sector(self):
        n=self.fixture();n.sequence=0;n.task_id='test';n.scans_at_viewpoint=1;n.scan_completed=True
        n.grid=NS(candidates=lambda *args,**kwargs:[])
        obs=SemanticNavigation.observation(n,[0,0,1])
        self.assertFalse(obs['scan_completed'])
        n.scan_completed=True;n.scans_at_viewpoint=n.runtime['scan']['max_sectors_per_viewpoint']
        obs=SemanticNavigation.observation(n,[0,0,1])
        self.assertTrue(obs['scan_completed'])

    def test_distractor_approach_does_not_suppress_extra_scan(self):
        n=self.fixture();n.sequence=0;n.task_id='test';n.scans_at_viewpoint=1;n.scan_completed=True
        n.memory.observe=lambda t:[{'id':'blue','category':'pipe','color':'blue'}]
        n.grid=NS(candidates=lambda *a,**k:[{'kind':'approach','object_id':'blue'}])
        obs=SemanticNavigation.observation(n,[0,0,1])
        self.assertEqual(obs['candidates'],[]);self.assertFalse(obs['scan_completed'])

    def test_scan_alignment_is_bounded(self):
        n=self.fixture();n.mode='SCAN_ALIGN';n.anchor=[0,0,1];n.hold_yaw=2.;n.action_started=10.
        self.tick(n);self.assertEqual(n.mode,'SCAN_ALIGN')
        n.time+=n.runtime['scan']['timeout_s']+.1;self.tick(n)
        self.assertEqual(n.mode,'SCANNING');self.assertEqual(n.scan_accum,0.)
        n.finish.assert_not_called()

    def test_target_during_scan_alignment_returns_to_decision(self):
        n=self.fixture();n.mode='SCAN_ALIGN';n.anchor=[0,0,1];n.hold_yaw=2.;n.action_started=10.
        n.memory.observe=lambda t:[{'confirmed':True,'category':'pipe','color':'yellow','visible_now':True}]
        self.tick(n);self.assertEqual(n.mode,'READY');self.assertTrue(n.scan_completed)
        n.finish.assert_not_called()

if __name__=='__main__':unittest.main()
