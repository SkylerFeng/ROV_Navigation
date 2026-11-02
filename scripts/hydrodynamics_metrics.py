"""Sampled dynamics diagnostics shared by exports and regression reports."""
import numpy as np


def dynamics_metrics(run, controls):
    impulses = [entry.get('max_impulse_norm', 0.) for entry in run.get('contacts', [])]
    result = {
        'physics_mode': run.get('physics_mode', 'legacy'),
        'max_contact_impulse_ns': max(impulses, default=0.),
    }
    if not controls:
        return result
    velocities = np.array([c['velocity'] for c in controls])
    desired = np.array([c['desired_velocity'] for c in controls])
    result['max_speed_m_s'] = float(np.linalg.norm(velocities, axis=1).max())
    result['velocity_error_rmse_m_s'] = float(np.sqrt(np.mean(np.sum((velocities-desired)**2, axis=1))))
    samples = np.array(run['samples'])
    result['max_depth_reference_error_m'] = float(np.abs(samples[:, 3]-run['config']['start'][2]).max())
    result['path_length_m'] = float(np.linalg.norm(np.diff(samples[:, 1:4], axis=0), axis=1).sum())
    records = [c['hydrodynamics'] for c in controls if c.get('hydrodynamics')]
    if records:
        result.update(
            current_world_m_s=records[0]['current_world_m_s'],
            force_saturation_sample_fraction=float(np.mean([r['force_saturated'] for r in records])),
            torque_saturation_sample_fraction=float(np.mean([r['torque_saturated'] for r in records])),
            min_submerged_fraction=min(r['submerged_fraction'] for r in records),
            max_actuator_force_n=float(np.abs([r['actuator_force_body_n'] for r in records]).max()),
            max_buoyancy_n=max(r['buoyancy_world_n'][2] for r in records),
        )
    return result
