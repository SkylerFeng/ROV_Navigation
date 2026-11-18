import unittest
from semantic_core import ExplorationGrid
from semantic_escape import inflation_escape,escape_segment_clear

class Escape(unittest.TestCase):
    def grid(self):
        g=ExplorationGrid([[-3,-3],[3,-3],[3,3],[-3,3]],.1,.4,inflation_metric='chessboard')
        g.free[:]=g.inside;g.occupied[g.cell([0,0])]=True;g.free[g.occupied]=False
        return g
    def test_safe_start_needs_no_escape(self):
        self.assertIsNone(inflation_escape(self.grid(),[1,1,1]))
    def test_actual_hull_overlap_cannot_be_escaped_blindly(self):
        self.assertIsNone(inflation_escape(self.grid(),[.15,.15,1]))
    def test_inflated_corner_can_escape_with_swept_certificate(self):
        e=inflation_escape(self.grid(),[.45,.35,1])
        self.assertIsNotNone(e)
        self.assertGreaterEqual(e['swept_min_obstacle_center_distance_m'],e['required_distance_m'])
    def test_new_obstacle_invalidates_recovery(self):
        g=self.grid();start=[.45,.35,1];goal=inflation_escape(g,start)['position']
        self.assertTrue(escape_segment_clear(g,start,goal))
        g.occupied[g.cell(goal)]=True;g.free[g.cell(goal)]=False
        self.assertFalse(escape_segment_clear(g,start,goal))
    def test_unknown_destinations_rejected(self):
        g=self.grid();g.free[:]=False;g.free[g.cell([.45,.35])]=True
        self.assertIsNone(inflation_escape(g,[.45,.35,1]))

if __name__=='__main__':unittest.main()
