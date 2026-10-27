"""Measured slalom diagnostics; old/new conditions are intentionally explicit."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    runs = []
    for directory, label, color in [(args.before, 'Before: not reached', '#c65c23'),
                                     (args.after, 'After: reached', '#198341')]:
        run = json.loads((directory/'run.json').read_text())
        controls = json.loads((directory/'controls.json').read_text())
        a = np.asarray(run['samples'])
        runs.append(run)
        axes[0, 0].plot(a[:, 1], a[:, 2], color=color, label=label, lw=2)
        axes[0, 0].scatter(*run['config']['start'][:2], color=color, s=35)
        error = np.linalg.norm(a[:, 1:4]-run['config']['goal'], axis=1)
        axes[0, 1].plot(a[:, 0], error, color=color, label=label)
        valid = [r for r in controls if (r.get('tracking') or {}).get('position_error') is not None]
        axes[1, 0].plot([r['t'] for r in valid],
                        [r['tracking']['position_error'] for r in valid], color=color, label=label, lw=1)
        valid = [r for r in controls if r.get('planner')]
        axes[1, 1].step([r['t'] for r in valid], [r['planner']['tracking_recoveries'] for r in valid],
                        where='post', color=color, label=label)
    for obj in runs[-1]['config']['obstacles']:
        x, y = obj['position'][:2]; sx, sy = obj['size'][:2]
        patch = (Circle((x, y), sx/2, color='tomato', alpha=.6) if obj.get('type') == 'cylinder'
                 else Rectangle((x-sx/2, y-sy/2), sx, sy, color='tomato', alpha=.6))
        axes[0, 0].add_patch(patch)
    axes[0, 0].scatter(*runs[-1]['config']['goal'][:2], marker='*', color='blue', s=100)
    axes[0, 0].set(xlabel='World X (m)', ylabel='World Y (m)', title='Actual recorded routes')
    axes[0, 0].set_aspect('equal')
    axes[0, 1].set(xlabel='Simulation time (s)', ylabel='Goal error (m)', title='Measured progress to final goal')
    axes[1, 0].axhline(.25, color='#777777', ls='--', label='Recovery threshold: 0.25 m')
    axes[1, 0].set(xlabel='Simulation time (s)', ylabel='Reference position error (m)', title='Tracking error at saved samples')
    axes[1, 1].set(xlabel='Simulation time (s)', ylabel='Cumulative recoveries', title='Measured-state trajectory resets')
    for ax in axes.flat:
        ax.grid(alpha=.25)
        ax.legend(fontsize=9)
    fig.suptitle('Slalom: measured navigation and tracking diagnostics', fontsize=15)
    before, after = runs
    fig.text(.5, .01,
             f"Before: start {before['config']['start']}, HFOV {before['config'].get('camera_horizontal_fov_deg',53.03):g} deg, stride {before.get('cloud_stride',4)}; "
             f"after: start {after['config']['start']}, HFOV {after['config'].get('camera_horizontal_fov_deg',53.03):g} deg, stride {after.get('cloud_stride',4)}.\n"
             f"Goal: {after['config']['goal']}; XY inflation 0.5 m. Curves are actual recorded samples without smoothing.",
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .065, 1, .96))
    for extension in ['png', 'svg', 'pdf']:
        fig.savefig(args.output/f'slalom_before_after.{extension}', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    main()
