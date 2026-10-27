"""Numerical oracle tests: EGO knot convention and independent SciPy spline."""
import unittest
import numpy as np
from scipy.interpolate import BSpline
from spline import sample_spline


class SplineTests(unittest.TestCase):
    def test_uniform_ego_knots(self):
        controls = np.random.default_rng(7).normal(size=(12, 3))
        knots = (np.arange(16)-3)*.2
        times, points = sample_spline(controls, knots, 3)
        np.testing.assert_allclose(points, BSpline(knots, controls, 3)(times+knots[3]), atol=1e-12)
        np.testing.assert_allclose(points[0], (controls[0]+4*controls[1]+controls[2])/6)

    def test_clamped_endpoints(self):
        controls = np.array([[0, 0, 1], [1, 2, 1], [2, -1, 1], [3, 0, 1]])
        knots = [0, 0, 0, 0, 1, 1, 1, 1]
        _, points = sample_spline(controls, knots, 3)
        np.testing.assert_allclose(points[[0, -1]], controls[[0, -1]])

    def test_reject_invalid_knots(self):
        with self.assertRaises(ValueError):
            sample_spline(np.zeros((4, 3)), [0, 0, 0, 1, 0, 1, 1, 1], 3)


if __name__ == "__main__":
    unittest.main()
