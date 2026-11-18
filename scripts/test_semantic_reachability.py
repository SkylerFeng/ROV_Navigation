import unittest,heapq,math
import numpy as np
from semantic_core import ExplorationGrid
from semantic_reachability import reachable

def scalar_reachable(self,start):
    root=self.cell(start);safe=self.safe();cost={};parent={}
    if not self.valid(root) or not self.free[root] or self.occupied[root]:return cost,parent
    # Newly observed geometry can put the current pose inside inflation.
    # Permit only monotonic-clearance escape in observed free cells, never
    # a new destination inside inflation or a route cutting through it.
    clearance=self.obstacle_clearance()
    def allowed(a,b):
        if not self.valid(b) or not self.free[b] or self.occupied[b] or not self.inside[b]:return False
        if safe[b]:return True
        return not safe[a] and clearance[b]>=clearance[a]-1e-9
    cost[root]=0.;queue=[(0.,root)]
    while queue:
        d,c=heapq.heappop(queue)
        if d>cost[c]:continue
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
            v=(c[0]+dx,c[1]+dy)
            if not allowed(c,v):continue
            if dx and dy and not(allowed(c,(c[0]+dx,c[1])) and allowed(c,(c[0],c[1]+dy))):continue
            nd=d+math.hypot(dx,dy)*self.res
            if nd<cost.get(v,float('inf')):cost[v]=nd;parent[v]=c;heapq.heappush(queue,(nd,v))
    return {c:d for c,d in cost.items() if safe[c]},parent

class Reachability(unittest.TestCase):
    def test_equivalent_costs_and_safe_edges(self):
        rng=np.random.default_rng(8)
        for metric in ('euclidean','chessboard'):
            for trial in range(8):
                g=ExplorationGrid([[-3,-2],[3,-2],[3,2],[-3,2]],.1,.3,inflation_metric=metric)
                g.free[:]=g.inside;g.occupied=rng.random(g.shape)<.008;g.free[g.occupied]=False
                old,_=scalar_reachable(g,[0,0,1]);new,parents=reachable(g,[0,0,1])
                self.assertEqual(old.keys(),new.keys())
                for cell in old:self.assertAlmostEqual(old[cell],new[cell])
                for cell,parent in parents.items():
                    self.assertTrue(g.free[cell]);self.assertFalse(g.occupied[cell])
                    self.assertLessEqual(max(abs(cell[i]-parent[i]) for i in (0,1)),1)
if __name__=='__main__':unittest.main()
