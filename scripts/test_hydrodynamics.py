"""Physics invariants and closed-loop disturbance rejection, independent of GPU."""
import math
import unittest
import numpy as np
from hydrodynamics import Hydrodynamics, VelocityController, parameters, rotation_matrix


POLYGON = [[-10, -10], [10, -10], [10, 10], [-10, 10]]
IDENTITY = [1, 0, 0, 0]


def model(**settings):
    return Hydrodynamics(settings, 2., -5., POLYGON)


class HydrodynamicsTests(unittest.TestCase):
    def test_passive_drag_always_dissipates_relative_energy(self):
        rng = np.random.default_rng(7)
        h = model()
        for _ in range(100):
            quat, velocity = rng.normal(size=4), rng.normal(size=3)
            _, _, info = h.step(.01, [0, 0, 0], quat, velocity, velocity, [0]*3, [0]*3)
            self.assertLessEqual(np.dot(info['drag_body_n'], info['relative_velocity_body']), 0)

    def test_flow_and_robot_comoving_have_zero_drag(self):
        h = model(current_world_m_s=[.1, -.1, .02])
        _, _, info = h.step(.01, [0, 0, 0], [.7, .2, -.1, .6], [.1, -.1, .02], [0]*3, [0]*3, [0]*3)
        np.testing.assert_allclose(info['drag_body_n'], 0, atol=1e-12)

    def test_current_rotates_into_body_axes(self):
        h = model(current_world_m_s=[.1, 0, 0])
        _, _, info = h.step(.01, [0, 0, 0], [math.sqrt(.5), 0, 0, math.sqrt(.5)], [0]*3, [0]*3, [0]*3, [0]*3)
        np.testing.assert_allclose(info['relative_velocity_body'], [0, .1, 0], atol=1e-12)

    def test_neutral_buoyancy_balances_physx_weight_once(self):
        h = model(displaced_volume_m3=.005)
        force, _, info = h.step(.01, [0, 0, 0], IDENTITY, [0, .08, 0], [0]*3, [0]*3, [0]*3)
        np.testing.assert_allclose(force+info['gravity_world_n'], 0, atol=1e-12)

    def test_partial_submersion_and_outside_water(self):
        h = model()
        self.assertAlmostEqual(h.submersion([0, 0, 2-.116], np.eye(3)), .5)
        for position in ([0, 0, 3], [11, 0, 0], [0, 0, -6]):
            force, torque, info = h.step(.01, position, IDENTITY, [0]*3, [0]*3, [0]*3, [0]*3)
            np.testing.assert_allclose(force, 0)
            self.assertEqual(info['submerged_fraction'], 0)

    def test_buoyancy_rights_roll_and_pitch_without_yaw_spring(self):
        for axis in (1, 2):
            q = np.zeros(4); q[0] = math.cos(.1); q[axis] = math.sin(.1)
            _, torque, _ = model().step(.01, [0, 0, 0], q, [0, .08, 0], [0]*3, [0]*3, [0]*3)
            self.assertLess(torque[axis-1], 0)
            self.assertAlmostEqual(torque[2], 0)

    def test_exact_actuator_time_constant_and_saturation(self):
        h = model(force_tau_s=.3)
        for _ in range(30):
            h.step(.01, [0, 0, 0], IDENTITY, [0]*3, [0]*3, [100, 0, 0], [0]*3)
        self.assertAlmostEqual(h.actuator_force[0], 12*(1-math.exp(-1)), places=10)
        self.assertLess(h.actuator_force[0], 12)

    def test_integrator_rejects_oblique_current_and_positive_buoyancy(self):
        settings = {'current_world_m_s': [.08, .04, 0]}
        h, servo = model(**settings), VelocityController(settings)
        velocity = np.zeros(3)
        for _ in range(3000):
            command, torque = servo.step(.01, IDENTITY, velocity, [0]*3, [0]*3, 0)
            force, _, info = h.step(.01, [0, 0, 0], IDENTITY, velocity, [0]*3, command, torque)
            velocity += .01*(force+info['gravity_world_n'])/h.p['mass_kg']
        self.assertLess(np.linalg.norm(velocity), 1e-4)
        self.assertLess(servo.integral_world[0], -.6)
        self.assertLess(servo.integral_world[2], -.4)

    def test_integral_stays_bounded_when_actuators_saturate(self):
        servo = VelocityController({})
        for _ in range(1000):
            servo.step(.01, IDENTITY, [0]*3, [0]*3, [20, 20, 20], 0)
        np.testing.assert_allclose(servo.integral_world, 0)

    def test_turning_does_not_rotate_world_integral_force(self):
        servo = VelocityController({})
        servo.integral_world = np.array([1., -.5, .2])
        q = [math.sqrt(.5), 0, 0, math.sqrt(.5)]
        command, _ = servo.step(.01, q, [0]*3, [0]*3, [0]*3, 0)
        np.testing.assert_allclose(rotation_matrix(q) @ command, [1., -.5, .2], atol=1e-12)

    def test_yaw_servo_limits_requested_rate(self):
        servo = VelocityController({})
        _, torque = servo.step(.01, IDENTITY, [0]*3, [0]*3, [0]*3, 10.)
        p = servo.p
        self.assertAlmostEqual(torque[2], p['angular_kp'][2]*.25+p['angular_drag'][2]*.25+p['quadratic_angular_drag'][2]*.25**2)

    def test_passive_robot_drifts_toward_flow(self):
        h = model(current_world_m_s=[.1, 0, 0], displaced_volume_m3=.005)
        velocity = np.zeros(3)
        for _ in range(1500):
            force, _, info = h.step(.01, [0, 0, 0], IDENTITY, velocity, [0]*3, [0]*3, [0]*3)
            velocity += .01*(force+info['gravity_world_n'])/5
        np.testing.assert_allclose(velocity, [.1, 0, 0], atol=1e-6)

    def test_invalid_physics_parameters_fail_early(self):
        for settings in ({'mass_kg': 0}, {'force_tau_s': -1}, {'linear_drag': [1, -1, 1]},
                         {'current_world_m_s': [float('nan'), 0, 0]}, {'typo': 1}):
            with self.assertRaises(ValueError):
                parameters(settings)


if __name__ == '__main__':
    unittest.main()
