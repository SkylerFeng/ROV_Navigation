import unittest
from types import SimpleNamespace as NS
import numpy as np
from semantic_debug import snapshot

class DebugTests(unittest.TestCase):
    def test_grid_orientation_and_read_only_snapshot(self):
        free=np.array([[False,True,True],[False,False,False]])
        g=NS(shape=(2,3),inside=np.array([[True]*3,[False,True,True]]),free=free,
             occupied=np.array([[False]*3,[False,True,False]]),origin=np.array([-1.,2.]),res=.15,
             safe=lambda:np.array([[False,True,False],[False]*3]))
        n=NS(grid=g,odom=None,now=lambda:1.,args=NS(policy='rule'),cfg={'instruction':'yellow box'},
             mode='READY',last_result='test',planner_state='',active=None,debug_decision=None,
             memory=NS(observe=lambda t:[]),path=[])
        before=free.copy();d=snapshot(n)
        self.assertEqual(d['grid']['cells'],[[0,2,3],[1,4,0]])
        np.testing.assert_array_equal(before,free)
        import json
        json.dumps(d,allow_nan=False)

if __name__=='__main__':unittest.main()
