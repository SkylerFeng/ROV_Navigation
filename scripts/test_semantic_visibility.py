import math,unittest
import numpy as np
from semantic_core import ExplorationGrid
from semantic_visibility import visible_gain

# Independent scalar ray reference, preserving the original observation contract.
def reference(g,cell,meaningful):
    visible=set();angles=np.linspace(-np.pi,np.pi,48,endpoint=False);ray_gains=[]
    for angle in angles:
        ray=set();direction=np.array([np.cos(angle),np.sin(angle)])
        for distance in np.arange(g.res,(g.inspection_range or 3.)+.01,g.res):
            c=g.cell(g.xy(cell)+direction*distance)
            if not g.valid(c) or not g.inside[c] or g.occupied[c]:break
            if meaningful[c]:visible.add(c);ray.add(c)
        ray_gains.append(len(ray))
    scores=[sum(v for a,v in zip(angles,ray_gains) if abs(math.atan2(math.sin(a-center),math.cos(a-center)))<=math.pi/3) for center in angles]
    preferred=math.atan2(sum(v*math.sin(a) for a,v in zip(angles,ray_gains)),sum(v*math.cos(a) for a,v in zip(angles,ray_gains)))
    best=max(range(len(angles)),key=lambda i:(scores[i],math.cos(angles[i]-preferred)))
    return len(visible),float(angles[best])

class Visibility(unittest.TestCase):
    def test_matches_scalar_rays_with_occlusions_and_boundaries(self):
        rng=np.random.default_rng(73)
        for res in (.05,.1,.15):
            g=ExplorationGrid([[-3,-2],[3,-2],[3,2],[-3,2]],res,.4,inspection_range=2.5)
            g.occupied=rng.random(g.shape)<.02;meaningful=(rng.random(g.shape)<.5)&g.inside
            for cell in rng.integers([0,0],g.shape,size=(30,2)):
                self.assertEqual(reference(g,cell,meaningful),visible_gain(g,cell,meaningful,True))

if __name__=='__main__':unittest.main()
