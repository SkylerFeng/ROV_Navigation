"""Race regression: explore API returns after a safe target approach appears."""
import unittest
from concurrent.futures import Future
from unittest.mock import Mock
from types import SimpleNamespace as NS
import test_semantic_recovery_ros as recovery

class DecisionRefreshTests(unittest.TestCase):
    def test_new_approach_requeries_without_executing_stale_explore(self):
        helper=recovery.RecoveryStateTests();n=helper.fixture();n.mode='DECIDING';n.sequence=12
        n.pending_observation={'observation_id':10,'candidates':[{'kind':'explore'}]}
        action={'action':'explore','task_id':'test','observation_id':10,'candidate_id':'vp','reason_code':'search'}
        old=Future();old.set_result((action,{}));n.future=old
        fresh={'observation_id':12,'candidates':[{'kind':'approach','object_id':'target','id':'near'}],'objects':[]}
        n.observation=lambda p:fresh;n.execute=Mock();new=Future()
        def request(p,yaw,obs):
            self.assertIs(obs,fresh);n.future=new
        n.decide=Mock(side_effect=request)
        helper.tick(n)
        n.execute.assert_not_called();n.decide.assert_called_once()
        self.assertIs(n.future,new);self.assertEqual(n.mode,'DECIDING')
        self.assertEqual(n.last_result,'target_confirmed_during_api_request')
        self.assertEqual(fresh['observation_id'],12)
        n.lease.assert_called_with('hold')
if __name__=='__main__':unittest.main()
