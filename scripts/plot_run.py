"""Export executed XY path and a conservative obstacle-clearance check."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

root = Path(__file__).resolve().parents[1]
r = json.loads((root / "logs/last_run.json").read_text())
c = r.get("config") or json.loads((root / "config/experiment.json").read_text())
path = np.array(r["samples"])
fig, ax = plt.subplots(figsize=(10, 5))
clearances = []
radius = np.hypot(.24, .285)
for obj in c["obstacles"]:
    center = np.array(obj["position"][:2])
    size = np.array(obj["size"][:2])
    ax.add_patch(Rectangle(center-size/2, *size, color="tomato"))
    ax.text(*center, obj["name"], ha="center", va="center", fontsize=9)
    delta = np.maximum(np.abs(path[:, 1:3]-center)-size/2, 0)
    clearances.append(float(np.linalg.norm(delta, axis=1).min()-radius))
ax.plot(path[:,1], path[:,2], color="green", label="Executed ROV path")
ax.scatter(*c["start"][:2], color="green", marker="o", label="Start")
ax.scatter(*c["goal"][:2], color="blue", marker="*", s=100, label="Goal")
ax.set(xlabel="World X (m)", ylabel="World Y (m)",
       title=f"ROV pool baseline | final goal error: {r['goal_distance']:.3f} m")
ax.set_aspect("equal")
ax.grid(alpha=.3)
ax.legend()
fig.tight_layout()
fig.savefig(root / "logs/executed_path.png", dpi=160)
image = np.load(root / "logs/last_camera.npy")
Image.fromarray(image[:,:,:3].astype(np.uint8)).save(root / "logs/last_camera.png")
result = {"goal_error_m": r["goal_distance"], "reached_within_0_3m": r["goal_distance"] < .3,
          "min_conservative_clearance_to_added_blocks_m": min(clearances),
          "note": "Clearance uses sampled XY positions and a circumscribed hull circle; not a PhysX contact count.",
          "depth_mode": r.get("depth_mode", "degraded")}
(root / "logs/navigation_validation.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
