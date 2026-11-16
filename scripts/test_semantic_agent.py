import unittest
from semantic_agent import TaskAgent,load_agent

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agent=TaskAgent(load_agent());self.c={'id':'vp','kind':'explore','position':[1,0,1],'score':3.,'reachable':True}
        self.obs={'observation_id':1,'candidates':[self.c]};self.action={'action':'explore','candidate_id':'vp'}
    def test_action_result_memory_changes_next_decision_options(self):
        a=self.agent;a.start(self.action,self.obs,0);r=a.complete('FAILED','blocked_goal',4)
        self.assertEqual(r['duration_s'],4);self.assertEqual(a.constrain([self.c],5),[])
        self.assertEqual(a.summary()['recent_results'][0]['reason'],'blocked_goal')
        self.assertEqual(a.constrain([self.c],60)[0]['previous_failures'],1)
        self.assertLess(a.constrain([self.c],60)[0]['score'],3)
        with self.assertRaises(ValueError):a.validate(self.action,5)
    def test_success_and_budget(self):
        a=self.agent
        for t in (0,60):a.start(self.action,self.obs,t);a.complete('SUCCEEDED','reached',t+2)
        self.assertEqual(a.summary()['visited_viewpoints'],['vp']);self.assertEqual(a.constrain([self.c],100),[])
    def test_hold_bound(self):
        a=self.agent
        for t in range(3):a.start({'action':'hold'},self.obs,t);a.complete('SUCCEEDED','hold_done',t+.5)
        with self.assertRaises(ValueError):a.validate({'action':'hold'},4)
    def test_spin_monitor_excludes_scan_and_detects_navigation(self):
        a=self.agent
        for i in range(30):self.assertIsNone(a.loop(i,[0,0,1],i*.25,'SCANNING'))
        result=None
        for i in range(30):result=a.loop(i+20,[0,0,1],i*.25,'EXPLORING')
        self.assertIsNotNone(result)
    def test_motion_and_clock_reset_not_spin(self):
        a=self.agent
        for i in range(15):self.assertIsNone(a.loop(i,[i*.1,0,1],i*.25,'EXPLORING'))
        self.assertIsNone(a.loop(0,[0,0,1],0,'EXPLORING'))
    def test_pending_approach_is_not_success(self):
        self.agent.start({'action':'approach','candidate_id':'vp'},self.obs,0)
        self.agent.update_phase('VERIFYING',[],{'category':'box','color':'red'})
        self.assertEqual(self.agent.phase,'VERIFY');self.assertIsNotNone(self.agent.current)
        self.assertEqual(self.agent.summary()['recent_results'],[])
if __name__=='__main__':unittest.main()
