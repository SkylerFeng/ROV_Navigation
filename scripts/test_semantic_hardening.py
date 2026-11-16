import unittest
import numpy as np
from semantic_core import ObjectMemory,ExplorationGrid
from static_collision_prior import seed_grid,load_static_xy
class Hardening(unittest.TestCase):
    def detection(self,cat,x=0):return dict(category=cat,color='yellow',surface_world=[x,0,1],detector_score=.8)
    def test_conflict_blocks_then_recovers(self):
        m=ObjectMemory(3)
        for i in range(4):m.update([self.detection('pipe')],i*.1)
        self.assertTrue(m.observe(.3)[0]['confirmed'])
        m.update([self.detection('box')],.4)
        self.assertEqual(len(m.objects),1)
        self.assertFalse(m.observe(.4)[0]['confirmed'])
        for i in range(5,12):m.update([self.detection('box')],i*.1)
        self.assertTrue(m.observe(1.1)[0]['confirmed'])
    def test_alternation_never_confirms(self):
        m=ObjectMemory(3)
        for i in range(20):
            m.update([self.detection(('pipe','box')[i%2])],i*.1)
            self.assertFalse(m.observe(i*.1)[0]['confirmed'])
    def test_adjacent_objects_stay_separate(self):
        m=ObjectMemory(3)
        for i in range(4):m.update([self.detection('pipe'),self.detection('box',.8)],i*.1)
        self.assertEqual(len(m.objects),2)
        self.assertTrue(all(o['confirmed'] for o in m.observe(.3)))
    def test_simultaneous_class_conflict(self):
        m=ObjectMemory(3)
        for i in range(6):m.update([self.detection('pipe'),self.detection('box',.01)],i*.1)
        self.assertEqual(len(m.objects),1)
        self.assertFalse(m.observe(.5)[0]['confirmed'])
    def test_pipe_surfaces_cannot_confirm_separate_box(self):
        m=ObjectMemory(3)
        for i in range(6):m.update([self.detection('pipe'),self.detection('box',.5)],i*.1)
        self.assertFalse(any(o['confirmed'] for o in m.observe(.5)))
    def test_large_confirmation_window(self):
        m=ObjectMemory(12)
        for i in range(12):m.update([self.detection('pipe')],i*.1)
        self.assertTrue(m.observe(1.1)[0]['confirmed'])
    def test_square_inflation_rejects_diagonal_corner(self):
        g=ExplorationGrid([[-2,-2],[2,-2],[2,2],[-2,2]],.1,.4,inflation_metric="chessboard")
        g.free[:]=g.inside;g.occupied[g.cell([0,0])]=True
        self.assertFalse(g.safe()[g.cell([.4,.4])])
        self.assertTrue(g.safe()[g.cell([.7,.7])])
    def test_prior_is_occupied_only(self):
        g=ExplorationGrid([[-6,-3],[6,-3],[6,3],[-6,3]])
        xy=load_static_xy({'static_collision_prior':'config/maps/platform_static_collision.npz'})
        seed_grid(g,xy)
        self.assertTrue(g.occupied.any());self.assertFalse(g.free.any())
        self.assertFalse(g.occupied[g.cell([-2,0])])
if __name__=='__main__':unittest.main()

class RegionTransfer(unittest.TestCase):
    def test_transit_can_reuse_inspected_space_but_never_unknown(self):
        g=ExplorationGrid([[-5,-2],[5,-2],[5,2],[-5,2]],.15,.4,inspection_range=2.5,inflation_metric='chessboard')
        g.free[:]=g.inside;g.inspected[:]=g.inside
        cs=g.candidates([2,0,1],[],settings={'coarse_region_xyxy':[-4,-1,-3,1],'region_transfer':True})
        transit=[c for c in cs if c.get('purpose')]
        self.assertEqual(len(transit),1);self.assertLess(transit[0]['position'][0],2)
        self.assertLessEqual(transit[0]['path_length_m'],2.)
        self.assertTrue(g.safe()[g.cell(transit[0]['position'])])
        g.free[:]=False;g._safe=None
        self.assertEqual(g.candidates([2,0,1],[],settings={'coarse_region_xyxy':[-4,-1,-3,1],'region_transfer':True}),[])
