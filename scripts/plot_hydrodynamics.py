"""Plot measured forces and velocities from a navigation run (no smoothing)."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(directory, output):
    run = json.loads((directory/'run.json').read_text())
    controls = json.loads((directory/'controls.json').read_text())
    controls = [c for c in controls if c.get('hydrodynamics')]
    if not controls:
        raise ValueError('No hydrodynamics telemetry in this run')
    t = np.array([c['t'] for c in controls])
    info = [c['hydrodynamics'] for c in controls]
    velocity = np.array([c['velocity'] for c in controls])
    desired = np.array([c['desired_velocity'] for c in controls])
    thrust = np.array([h['actuator_force_body_n'] for h in info])
    target = np.array([h['force_target_body_n'] for h in info])
    buoyancy = np.array([h['buoyancy_world_n'][2] for h in info])
    weight = np.array([-h['gravity_world_n'][2] for h in info])
    samples = np.array(run['samples'])
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    ax = axes[0, 0]
    for i, name in enumerate('XY'):
        ax.plot(t, velocity[:, i], label=f'Actual {name}', color=f'C{i}')
        ax.plot(t, desired[:, i], '--', alpha=.7, label=f'Target {name}', color=f'C{i}')
    ax.set(ylabel='World velocity (m/s)', title='Velocity tracking with water current')
    ax = axes[0, 1]
    for i, name in enumerate('XY'):
        ax.plot(t, thrust[:, i], label=f'Actuator {name}', color=f'C{i}')
        ax.plot(t, target[:, i], '--', alpha=.7, label=f'Target {name}', color=f'C{i}')
    ax.set(ylabel='Body force (N)', title='Actuator lag (force is limited before filtering)')
    ax = axes[1, 0]
    ax.plot(t, buoyancy, label='Buoyancy')
    ax.plot(t, weight, '--', label='Weight magnitude')
    ax.set(ylabel='Force (N)', title='Explicit buoyancy and gravity')
    ax = axes[1, 1]
    error = np.linalg.norm(samples[:, 1:4]-run['config']['goal'], axis=1)
    ax.semilogy(samples[:, 0], np.maximum(error, 1e-7), label='Measured goal error')
    ax.axhline(run['arrival_tolerance'], linestyle='--', color='gray', label='Arrival tolerance')
    ax.set(ylabel='Goal error (m)', title='Actual goal approach')
    for ax in axes.flat:
        ax.set_xlabel('Simulation time (s)')
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle(f"{run['scenario']} | current {info[0]['current_world_m_s']} m/s | "
                 f"error {run['goal_distance']:.4f} m")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plot(args.directory, args.output)
