"""Overview of configured layouts without invented planned trajectories."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from experiment import ROOT, load_experiment

names = list(json.loads((ROOT / "config/scenarios.json").read_text()))
fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=True, sharey=True)
for ax, name in zip(axes.flat, names):
    c = load_experiment(name)
    for obj in c["obstacles"]:
        x, y = obj["position"][:2]
        sx, sy = obj["size"][:2]
        if obj.get("type") == "cylinder":
            patch = Circle((x, y), sx/2, color="#26a5c0")
        else:
            patch = Rectangle((x-sx/2, y-sy/2), sx, sy, color="#e66b43")
        ax.add_patch(patch)
    ax.scatter(*c["start"][:2], color="green", label="Start")
    ax.scatter(*c["goal"][:2], marker="*", s=90, color="blue", label="Goal")
    ax.set(title=f"{name} | {len(c['obstacles'])} obstacles", xlim=(-3.5, 4.3), ylim=(-2.1, 3.2))
    ax.set_aspect("equal"); ax.grid(alpha=.2)
axes.flat[-1].axis("off")
axes.flat[-1].text(.05, .7, "ROV pool test layouts\n\nBoxes / wall segments: orange\nPillars: blue\n\nCoordinates in meters\nFixed depth: 1.0 m", fontsize=13)
fig.tight_layout()
fig.savefig(ROOT / "logs/scenarios_overview.png", dpi=150)
