"""Check geometry dependence, energy, local rotations and integration selection."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from component_hydrodynamics import ComponentHydrodynamics, ROOT
from hydrodynamics import Hydrodynamics, parameters


class ComponentTests(unittest.TestCase):
    def settings(self, path):
        return parameters(dict(component_model_file=str(path), current_world_m_s=[0, 0, 0]))

    def patch(self, directory, normal=(1, 0, 0), center=(0, 0, .216), area=2.):
        p = Path(directory)/'surface.json'
        p.write_text(json.dumps(dict(schema_version=1, cell_size_m=.04,
           patches=dict(centers_body_m=[center], normals_body=[normal], area_m2=[area], component_ids=[7]))))
        return p

    def test_normal_tangent_area_and_moment(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.patch(d);h=ComponentHydrodynamics(self.settings(p))
            f,t,_=h.wrench([.2,0,0],[0,0,0])
            np.testing.assert_allclose(f,[-20,0,0])
            np.testing.assert_allclose(t,[0,-2,0])
            tangent,_,_=h.wrench([0,.2,0],[0,0,0])
            np.testing.assert_allclose(tangent,[0,-.2,0])
            h2=ComponentHydrodynamics(self.settings(self.patch(d,area=4)))
            np.testing.assert_allclose(h2.wrench([.2,0,0],[0,0,0])[0],2*f)

    def test_passivity_with_rotation_and_partial_wetting(self):
        path=ROOT/'config/hydrodynamic_components/bluerov_mesh.json'
        h=ComponentHydrodynamics(self.settings(path));rng=np.random.default_rng(92)
        for _ in range(12):
            v,w=rng.normal(size=(2,3))
            f,t,info=h.wrench(v,w,rng.uniform(size=h.patch_count))
            power=float(f@v+t@w)
            self.assertLessEqual(power,1e-10)
            self.assertAlmostEqual(power,info['relative_drag_power_w'],places=8)

    def test_normals_control_direction_and_pure_rotation(self):
        with tempfile.TemporaryDirectory() as d:
            h=ComponentHydrodynamics(self.settings(self.patch(d,normal=(0,1,0),center=(.2,0,.116))))
            f,t,_=h.wrench([0,0,0],[0,0,1])
            self.assertLess(t[2],0)
            self.assertLess(f[1],0)

    def test_dry_patches_and_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            h=ComponentHydrodynamics(self.settings(self.patch(d)))
            for pos in [[0,0,3],[0,0,-3],[5,0,0]]:
                wet=h.wet_fractions(pos,np.eye(3),2,-2,[[-1,-1],[1,-1],[1,1],[-1,1]])
                np.testing.assert_allclose(h.wrench([.2,0,0],[0,0,1],wet)[0],0)

    def test_component_path_replaces_legacy_drag(self):
        with tempfile.TemporaryDirectory() as d:
            s=dict(component_model_file=str(self.patch(d)),current_world_m_s=[0,0,0])
            h=Hydrodynamics(s,2,-2,[[-1,-1],[1,-1],[1,1],[-1,1]])
            _,_,info=h.step(.01,[0,0,0],[1,0,0,0],[.2,0,0],[0,0,0],[0]*3,[0]*3)
            np.testing.assert_allclose(info['drag_body_n'],[-20,0,0])
            self.assertEqual(info['component_hydrodynamics']['component_count'],1)

    def test_bad_normal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                ComponentHydrodynamics(self.settings(self.patch(d,normal=(0,0,0))))


if __name__=='__main__':
    unittest.main()
