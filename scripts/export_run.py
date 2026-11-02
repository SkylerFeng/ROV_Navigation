"""Export measured results and an animation of actual EGO plan revisions."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation, PillowWriter
from hydrodynamics_metrics import dynamics_metrics


def export(directory, animate=True):
    directory = Path(directory)
    r = json.loads((directory / "run.json").read_text())
    c, samples = r["config"], np.array(r["samples"])
    plans = json.loads((directory / "plans.json").read_text())
    radius = np.hypot(.24, .285)
    clearances = []
    for obj in c["obstacles"]:
        delta = np.abs(samples[:,1:3]-np.array(obj["position"][:2]))
        if obj.get("type") == "cylinder":
            distances = np.linalg.norm(delta, axis=1)-obj["size"][0]/2
        else:
            distances = np.linalg.norm(np.maximum(delta-np.array(obj["size"][:2])/2, 0), axis=1)
        clearances.append(float(distances.min()-radius))
    metrics = {"scenario": r["scenario"], "goal_error_m": r["goal_distance"],
               "goal_reached": r["stop_reason"] == "goal_reached" if "arrival_tolerance" in r else r["goal_distance"] < c.get("goal_tolerance", .3), "plan_updates": r["plan_updates"],
               "stop_reason": r["stop_reason"], "simulation_seconds": r.get("simulation_seconds", float(samples[-1,0])),
               "conservative_block_clearance_m": min(clearances) if clearances else None,
               "depth_mode": r["depth_mode"],
               "note": "Single trial; clearance is a sampled circumscribed-hull bound, not a contact count."}
    control_file = directory / "controls.json"
    metrics.update(dynamics_metrics(r, json.loads(control_file.read_text()) if control_file.exists() else []))
    (directory / "metrics.json").write_text(json.dumps(metrics, indent=2))
    fig, ax = plt.subplots(figsize=(10, 6))
    geometry = directory / "pool_collision_sections.json"
    if geometry.exists():
        from matplotlib.collections import LineCollection
        sections = json.loads(geometry.read_text())
        ax.add_collection(LineCollection(sections["segments"], colors="#555555", linewidths=.7, label="Scanned collision slices"))
    if c.get("water_boundary"):
        boundary_file = directory / "sources" / c["water_boundary"]
        if not boundary_file.exists():
            boundary_file = Path(__file__).resolve().parents[1] / c["water_boundary"]
        boundary = np.array(json.loads(boundary_file.read_text()))
        boundary = np.vstack((boundary, boundary[0]))
        ax.plot(boundary[:,0], boundary[:,1], "--", color="#5588bb", label="Configured water boundary")
    for obj in c["obstacles"]:
        x, y = obj["position"][:2]; sx, sy = obj["size"][:2]
        patch = Circle((x,y), sx/2, color="#26a5c0") if obj.get("type") == "cylinder" else Rectangle((x-sx/2,y-sy/2),sx,sy,color="#e66b43")
        ax.add_patch(patch)
    ax.scatter(*c["start"][:2], color="green", label="Start")
    ax.scatter(*c["goal"][:2], color="blue", marker="*", s=100, label="Goal")
    actual, = ax.plot([], [], color="#159934", lw=2.5, label="Executed")
    old_lines = [ax.plot([], [], color="#eaa13c", alpha=.45, lw=1.5, label="Previous plans" if i==0 else None)[0] for i in range(3)]
    current, = ax.plot([], [], color="#00b8d4", lw=2.5, label="Current EGO plan")
    robot, = ax.plot([], [], "o", color="#159934")
    ax.set(xlim=(-3.6,4.3), ylim=(-2.1,3.3), xlabel="World X (m)", ylabel="World Y (m)")
    if c["scenario"].startswith("highbay"):
        ax.set_xlim(-5.3, 5.3); ax.set_ylim(-2.7, 2.7)
    ax.set_aspect("equal"); ax.grid(alpha=.2); ax.legend(loc="lower right")
    def draw(index):
        time = plans[index]["start_time"] if plans else samples[-1,0]
        visible = samples[samples[:,0] <= time]
        if not len(visible):
            visible = samples[:1]
        actual.set_data(visible[:,1], visible[:,2]); robot.set_data(visible[-1:,1], visible[-1:,2])
        for line in old_lines:
            line.set_data([], [])
        if plans:
            curve = np.array(plans[index]["points"])
            current.set_data(curve[:,0], curve[:,1])
            for line, previous in zip(old_lines, plans[max(0,index-3):index]):
                xy = np.array(previous["points"]); line.set_data(xy[:,0], xy[:,1])
        ax.set_title(f"{r['scenario']} | plan revision {index+1}/{len(plans)} | sim time {time:.1f} s")
    draw(max(0,len(plans)-1))
    actual.set_data(samples[:,1],samples[:,2]);robot.set_data(samples[-1:,1],samples[-1:,2])
    ax.set_title(f"{r['scenario']} | goal error {r['goal_distance']:.3f} m | {r['plan_updates']} plan updates")
    fig.tight_layout();fig.savefig(directory / "trajectory_updates.png",dpi=150)
    if animate and plans:
        # Stop-at-goal snapshots have very few late revisions; preserve the whole run.
        indices = np.unique(np.linspace(0,len(plans)-1,min(50,len(plans))).astype(int))
        animation = FuncAnimation(fig, draw, frames=indices, interval=180, repeat=True)
        animation.save(directory / "trajectory_updates.gif", writer=PillowWriter(fps=6))
    plt.close(fig)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--no-animation", action="store_true")
    args = parser.parse_args()
    print(json.dumps(export(args.directory, not args.no_animation), indent=2))
