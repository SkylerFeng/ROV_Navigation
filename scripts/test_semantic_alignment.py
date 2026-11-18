import unittest,math
import numpy as np
from semantic_alignment import entry_heading
from semantic_core import ExplorationGrid

class Alignment(unittest.TestCase):
    def test_heading_follows_detour_not_direct_goal_through_wall(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],.1,.3);g.free[:]=g.inside
        for y in np.arange(-2,.71,.1):g.occupied[g.cell([0,y])]=True
        g.free &= ~g.occupied
        heading=entry_heading(g,[-.6,0,1],[1,0,1])
        self.assertGreater(math.sin(heading),.5)
    def test_unreachable_goal_has_no_heading(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],.1,.3)
        self.assertIsNone(entry_heading(g,[0,0,1],[1,0,1]))
if __name__=='__main__':unittest.main()
