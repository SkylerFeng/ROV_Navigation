"""Reduced-order ROV dynamics and velocity servo; no Isaac/ROS dependencies.

All public velocities/forces are world-frame; drag and actuator limits are
body-frame. Gravity is supplied by PhysX, NOT included in returned force.
Coefficients are experiment parameters, not identified BlueROV parameters.
"""
import math
import numpy as np


DEFAULTS = {
    "mass_kg": 5.0,
    "density_kg_m3": 1000.0,
    "gravity_m_s2": 9.81,
    "displaced_volume_m3": 0.00505,
    "center_of_mass_body_m": [0.0, 0.0, 0.116],
    "center_of_buoyancy_offset_m": [0.0, 0.0, 0.025],
    "hull_size_m": [0.48, 0.57, 0.26],
    "inertia_kg_m2": [0.1635, 0.1242, 0.2314],
    "linear_drag": [8.0, 12.0, 16.0],
    "quadratic_drag": [12.0, 18.0, 24.0],
    "angular_drag": [0.18, 0.18, 0.15],
    "quadratic_angular_drag": [0.12, 0.12, 0.10],
    "current_world_m_s": [0.0, 0.08, 0.0],
    "force_limit_n": [12.0, 12.0, 15.0],
    "torque_limit_nm": [1.5, 1.5, 1.0],
    "force_tau_s": 0.25,
    "torque_tau_s": 0.12,
    "velocity_kp": [30.0, 30.0, 35.0],
    "velocity_ki": [8.0, 8.0, 12.0],
    "integral_limit_n": [5.0, 5.0, 5.0],
    "angular_kp": [1.2, 1.2, 1.0],
    "max_yaw_rate_rad_s": 0.25,
}


def parameters(overrides=None):
    overrides = overrides or {}
    unknown = set(overrides) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown hydrodynamics parameters: {sorted(unknown)}")
    result = {}
    unrestricted = {"current_world_m_s", "center_of_mass_body_m", "center_of_buoyancy_offset_m"}
    zeros_allowed = {"force_tau_s", "torque_tau_s", "linear_drag", "quadratic_drag",
                     "angular_drag", "quadratic_angular_drag", "velocity_ki"}
    for key, default in DEFAULTS.items():
        value = np.asarray(overrides.get(key, default), dtype=float)
        shape = (3,) if isinstance(default, list) else ()
        if value.shape != shape or not np.all(np.isfinite(value)):
            raise ValueError(f"Invalid {key}: expected finite shape {shape}")
        if key not in unrestricted and np.any(value < 0 if key in zeros_allowed else value <= 0):
            raise ValueError(f"Invalid non-positive hydrodynamics parameter: {key}")
        result[key] = value.copy() if shape else float(value)
    return result


def rotation_matrix(quaternion):
    q = np.asarray(quaternion, dtype=float)
    if q.shape != (4,) or not np.all(np.isfinite(q)) or np.linalg.norm(q) < 1e-12:
        raise ValueError("Expected a finite nonzero wxyz quaternion")
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def inside_polygon(xy, polygon):
    x, y = xy
    inside = False
    previous = polygon[-1]
    for point in polygon:
        x1, y1 = previous
        x2, y2 = point
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            inside = not inside
        previous = point
    return inside


class Hydrodynamics:
    def __init__(self, settings, surface_z, bottom_z, boundary_xy):
        self.p = parameters(settings)
        self.surface = float(surface_z)
        self.bottom = float(bottom_z)
        self.boundary = np.asarray(boundary_xy, dtype=float)
        if not math.isfinite(self.surface) or not math.isfinite(self.bottom) or self.surface <= self.bottom:
            raise ValueError("Water surface must be above bottom")
        if self.boundary.ndim != 2 or self.boundary.shape[1] != 2 or len(self.boundary) < 3 or not np.all(np.isfinite(self.boundary)):
            raise ValueError("Expected a finite water polygon")
        self.actuator_force = np.zeros(3)
        self.actuator_torque = np.zeros(3)

    def submersion(self, position, rotation):
        center = np.asarray(position) + rotation @ self.p["center_of_mass_body_m"]
        # Continuous vertical overlap of the oriented hull's bounding box.
        # This is a volume-fraction approximation near the surface, not CFD.
        height = np.abs(rotation[2]) @ self.p["hull_size_m"]
        lower, upper = center[2]-height/2, center[2]+height/2
        overlap = max(0.0, min(upper, self.surface)-max(lower, self.bottom))
        return float(np.clip(overlap/height, 0, 1)) if inside_polygon(center[:2], self.boundary) else 0.0

    def step(self, dt, position, quaternion, velocity_world, angular_world,
             force_command_body, torque_command_body):
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be positive simulation time")
        p = self.p
        rotation = rotation_matrix(quaternion)
        fraction = self.submersion(position, rotation)
        relative = rotation.T @ (np.asarray(velocity_world)-p["current_world_m_s"])
        angular = rotation.T @ np.asarray(angular_world)
        drag = -fraction*(p["linear_drag"]*relative + p["quadratic_drag"]*np.abs(relative)*relative)
        angular_drag = -fraction*(p["angular_drag"]*angular + p["quadratic_angular_drag"]*np.abs(angular)*angular)
        buoyancy_world = np.array([0., 0., fraction*p["density_kg_m3"]*p["displaced_volume_m3"]*p["gravity_m_s2"]])
        buoyancy_torque = np.cross(p["center_of_buoyancy_offset_m"], rotation.T @ buoyancy_world)
        force_target = np.clip(force_command_body, -p["force_limit_n"], p["force_limit_n"])
        torque_target = np.clip(torque_command_body, -p["torque_limit_nm"], p["torque_limit_nm"])
        for state, target, tau in [(self.actuator_force, force_target, p["force_tau_s"]),
                                   (self.actuator_torque, torque_target, p["torque_tau_s"])]:
            alpha = -math.expm1(-dt/tau) if tau > 0 else 1.0
            state += alpha*(target-state)
        force_world = rotation @ (self.actuator_force+drag) + buoyancy_world
        torque_world = rotation @ (self.actuator_torque+angular_drag+buoyancy_torque)
        details = {
            "submerged_fraction": fraction,
            "current_world_m_s": p["current_world_m_s"].tolist(),
            "relative_velocity_body": relative.tolist(), "drag_body_n": drag.tolist(),
            "angular_drag_body_nm": angular_drag.tolist(),
            "actuator_force_body_n": self.actuator_force.tolist(),
            "actuator_torque_body_nm": self.actuator_torque.tolist(),
            "force_target_body_n": force_target.tolist(),
            "torque_target_body_nm": torque_target.tolist(),
            "buoyancy_world_n": buoyancy_world.tolist(),
            "buoyancy_torque_body_nm": buoyancy_torque.tolist(),
            "gravity_world_n": [0., 0., -p["mass_kg"]*p["gravity_m_s2"]],
            "force_saturated": bool(np.any(np.abs(force_command_body) > p["force_limit_n"])),
            "torque_saturated": bool(np.any(np.abs(torque_command_body) > p["torque_limit_nm"])),
        }
        return force_world, torque_world, details


class VelocityController:
    """PI velocity servo; integral rejects steady current without observing it."""
    def __init__(self, settings):
        self.p = parameters(settings)
        # Store the integral in world axes so turning does not rotate its force.
        self.integral_world = np.zeros(3)

    def step(self, dt, quaternion, velocity_world, angular_world, desired_world, yaw_rate):
        rotation = rotation_matrix(quaternion)
        p = self.p
        error = rotation.T @ (np.asarray(desired_world)-np.asarray(velocity_world))
        integral = rotation.T @ self.integral_world
        candidate = np.clip(integral+p["velocity_ki"]*error*dt,
                            -p["integral_limit_n"], p["integral_limit_n"])
        output = p["velocity_kp"]*error+candidate
        # Integrate when unsaturated or when the error brings force out of saturation.
        accept = (np.abs(output) <= p["force_limit_n"]) | (error*output < 0)
        integral = np.where(accept, candidate, integral)
        integral = np.clip(integral, -p["integral_limit_n"], p["integral_limit_n"])
        self.integral_world = rotation @ integral
        force = p["velocity_kp"]*error+integral
        yaw_rate = float(np.clip(yaw_rate, -p["max_yaw_rate_rad_s"], p["max_yaw_rate_rad_s"]))
        desired_angular = rotation.T @ np.array([0., 0., yaw_rate])
        angular = rotation.T @ np.asarray(angular_world)
        torque = p["angular_kp"]*(desired_angular-angular)
        torque += p["angular_drag"]*desired_angular + p["quadratic_angular_drag"]*np.abs(desired_angular)*desired_angular
        return force, torque
