"""Plot measured Platform trajectories and archive compact, auditable evidence."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--suite', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    names = ['platform_ego_slalom', 'platform_ego_gates', 'platform_ego_mixed']
    titles = ['Staggered blocks', 'Two gates (corridor control)', 'Mixed boxes and pillars']
    a.output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharex=True, sharey=True)
    provenance = {}
    summary = []
    for ax, name, title in zip(axes, names, titles):
        src = a.suite / name
        r = json.loads((src / 'run.json').read_text())
        m = json.loads((src / 'metrics.json').read_text())
        summary.append(m)
        dst = a.output / name
        dst.mkdir(exist_ok=True)
        provenance[name] = {'source_directory': str(src.resolve()), 'sha256': {}}
        for filename in ['run.json', 'plans.json', 'metrics.json', 'scene_evidence.json', 'manifest.json', 'trajectory_updates.png', 'trajectory_updates.gif']:
            file = src / filename
            if file.exists():
                shutil.copy2(file, dst / filename)
                provenance[name]['sha256'][filename] = hashlib.sha256(file.read_bytes()).hexdigest()
        c = r['config']
        for obj in c['obstacles']:
            x, y = obj['position'][:2]
            sx, sy = obj['size'][:2]
            patch = Circle((x, y), sx/2, color='#ea8459') if obj.get('type') == 'cylinder' else Rectangle((x-sx/2, y-sy/2), sx, sy, color='#ea8459')
            ax.add_patch(patch)
        xy = np.array(r['samples'])[:, 1:3]
        xy = np.vstack([xy, r['final_position'][:2]])
        ax.plot(*xy.T, color='#15834b', lw=2, label='Measured ROV path')
        ax.scatter(*c['start'][:2], c='green', label='Start', zorder=4)
        ax.scatter(*c['goal'][:2], c='blue', marker='*', s=120, label='Goal', zorder=4)
        ax.set_title(f"{title}\n{'Reached' if m['goal_reached'] else 'Not reached'} | error {m['goal_error_m']:.3f} m")
        ax.set(xlim=(-2.6, 2.7), ylim=(-2.1, 2.3), xlabel='World X (m)', aspect='equal')
        ax.grid(alpha=.2)
        ax.text(.03, .03, f"{m['simulation_seconds']:.1f} s | {m['path_length_m']:.2f} m | {m['plan_updates']} EGO updates", transform=ax.transAxes, fontsize=9, bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
    axes[0].set_ylabel('World Y (m)')
    axes[-1].legend(loc='upper right', fontsize=8)
    fig.suptitle('Platform water + hydrodynamics | A* + EGO | current (0, 0.08, 0) m/s\nLocal route view; full configured boundary is shown in individual figures')
    fig.tight_layout()
    for ext in ['png', 'pdf', 'svg']:
        fig.savefig(a.output / f'three_routes.{ext}', dpi=180)
    plt.close(fig)
    (a.output / 'sources.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (a.output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
