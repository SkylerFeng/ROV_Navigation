import unittest,math
import numpy as np
from cloud_inflation import inflate_columns
class Inflation(unittest.TestCase):
    def test_empty_and_diagonal_footprint(self):
        self.assertEqual(inflate_columns([], .05, .4, True).shape,(0,2))
        cells=set(map(tuple,inflate_columns([[0,0]],.05,.4,True)))
        self.assertIn((8,0),cells);self.assertNotIn((8,8),cells)
    def test_matches_per_point_ego_xy_union(self):
        cells=np.array([[0,0],[1,2],[-8,4],[5,-3]])
        for radius,res in ((.4,.05),(.25,.1)):
            for circular in (True,False):
                step=math.ceil(radius/res);expected=set()
                for a,b in cells:
                    for x in range(-step,step+1):
                        for y in range(-step,step+1):
                            if not circular or math.hypot(x,y)*res<=radius+math.sqrt(.5)*res:expected.add((a+x,b+y))
                self.assertEqual(set(map(tuple,inflate_columns(cells,res,radius,circular))),expected)
if __name__=='__main__':unittest.main()
