"""Plot measured attitude, braking ablations and archive review evidence."""
import argparse
import hashlib
import json
from itertools import product
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from hydrodynamics import inside_polygon, rotation_matrix

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def audit_attitude(directory):
    run = read(directory / "run.json")
    rows = read(directory / "controls.json")
    config = run["config"]
    p = config["hydrodynamics"]
    rotations = np.array([rotation_matrix(row["orientation"]) for row in rows])
    samples = np.array(run["samples"])
    assert len(samples) == len(rows)
    centers = samples[:, 1:4] + rotations @ np.array(p["center_of_mass_body_m"])
    radius = float(np.linalg.norm(p["hull_size_m"]) / 2)
    clearances = []
    for obstacle in config["obstacles"]:
        # A sphere around the oriented hull versus a box enclosing each obstacle.
        # The box enclosing a cylinder is deliberately more conservative.
        delta = np.abs(centers - obstacle["position"]) - np.array(obstacle["size"]) / 2
        clearances.append(float(np.linalg.norm(np.maximum(delta, 0), axis=1).min() - radius))
    body_corners = np.array(list(product([-.5, .5], repeat=3))) * p["hull_size_m"]
    corners = centers[:, None, :] + np.einsum("nij,kj->nki", rotations, body_corners)
    boundary = read(ROOT / config["water_boundary"])
    bottom_margin = float(corners[:, :, 2].min() - config["pool_floor"])
    surface_margin = float(config["water_surface"] - corners[:, :, 2].max())
    all_inside = all(inside_polygon(point[:2], boundary) for point in corners.reshape(-1, 3))
    return dict(
        minimum_obstacle_sphere_to_box_clearance_m=min(clearances) if clearances else None,
        minimum_hull_corner_above_fluid_bottom_m=bottom_margin,
        minimum_hull_corner_below_surface_m=surface_margin,
        all_sampled_hull_corners_inside_boundary=all_inside,
        passed=bool(all_inside and bottom_margin > 0 and surface_margin > 0
                    and (not clearances or min(clearances) > 0)),
        note="Recorded attitude-aware sampled bound; fluid bottom is not necessarily the scanned floor. No swept collision guarantee.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--strong-current", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    validation = ROOT / "docs/validation/hydrodynamics_coupled_20261102"
    validation.mkdir(parents=True, exist_ok=True)
    probe = read(args.probe)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for name, label in [("level_brake_centred", "Centred force"), ("level_brake", "Thrust line +45 mm"),
                        ("level_brake_reverse", "Thrust line -45 mm")]:
        rows = probe["cases"][name]
        t = [r["t"] for r in rows]
        axes[0, 0].plot(t, [r["nose_up_deg"] for r in rows], label=label)
        axes[0, 1].plot(t, [r["velocity"][0] for r in rows], label=label)
    for ax in axes[0]:
        ax.axvspan(0, .5, color="orange", alpha=.15, label="-6 N brake command")
        ax.set_xlim(0, 8)
    axes[0, 0].set_ylabel("Nose-up angle (deg)")
    axes[0, 1].set_ylabel("World X velocity (m/s)")
    for name in ["centred_baseline", "coupled_acceleration", "no_added_mass"]:
        rows = probe["cases"][name]
        axes[1, 0].plot([r["t"] for r in rows], [r["nose_up_deg"] for r in rows], label=name)
    axes[1, 0].axvspan(6, 6.5, color="orange", alpha=.15)
    axes[1, 0].set_ylabel("Acceleration / braking pitch (deg)")
    rows = probe["cases"]["sway_stop"]
    axes[1, 1].plot([r["t"] for r in rows], [r["roll_deg"] for r in rows], label="Sway: accelerate then stop")
    axes[1, 1].set_ylabel("Roll angle (deg)")
    for ax in axes.flat:
        ax.set_xlabel("Simulation time (s)")
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle("Measured PhysX response | synthetic geometry / inertia hypotheses")
    fig.tight_layout()
    fig.savefig(args.output / "braking_ablations.png", dpi=170)
    plt.close(fig)
    compact_probe = {key: value for key, value in probe.items() if key != "cases"}
    compact_probe["cases"] = {name: rows[::12] for name, rows in probe["cases"].items()}
    (validation / "physx_probe.json").write_text(json.dumps(compact_probe, indent=2))

    names = ["platform_ego_slalom", "platform_ego_gates", "platform_ego_mixed"]
    fig, axes = plt.subplots(3, 3, figsize=(16, 10))
    audits = {}
    for col, name in enumerate(names):
        directory = args.suite / name
        run = read(directory / "run.json")
        rows = read(directory / "controls.json")
        t = np.array([r["t"] for r in rows])
        rotations = np.array([rotation_matrix(r["orientation"]) for r in rows])
        pitch = np.degrees(np.arcsin(np.clip(rotations[:, 2, 0], -1, 1)))
        roll = np.degrees(np.arctan2(rotations[:, 2, 1], rotations[:, 2, 2]))
        axes[0, col].plot(t, pitch, label="Nose-up")
        axes[0, col].plot(t, roll, label="Roll")
        axes[0, col].set_title(name)
        axes[0, col].set_ylabel("Attitude (deg)")
        axes[1, col].plot(t, np.linalg.norm([r["velocity"] for r in rows], axis=1), label="Actual speed")
        axes[1, col].plot(t, np.linalg.norm([r["desired_velocity"] for r in rows], axis=1), label="Requested speed", alpha=.7)
        axes[1, col].set_ylabel("Speed (m/s)")
        axes[2, col].plot(np.array(run["samples"])[:, 0], np.array(run["samples"])[:, 3], label="Actual Z")
        axes[2, col].axhline(run["config"]["start"][2], ls="--", color="gray", label="Reference Z")
        axes[2, col].set_ylabel("ROV origin Z (m)")
        audits[name] = audit_attitude(directory)
        dst = validation / name
        dst.mkdir(exist_ok=True)
        for filename in ["run.json", "plans.json", "metrics.json", "manifest.json", "scene_evidence.json"]:
            shutil.copy2(directory / filename, dst / filename)
        (dst / "controls_sampled.json").write_text(json.dumps(rows, separators=(",", ":")))
        (dst / "attitude_geometry_audit.json").write_text(json.dumps(audits[name], indent=2))
    for ax in axes.flat:
        ax.set_xlabel("Simulation time (s)")
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle("A* + EGO navigation with coupled hydrodynamics | current Y = 0.08 m/s")
    fig.tight_layout()
    fig.savefig(args.output / "navigation_attitude.png", dpi=170)
    plt.close(fig)
    extras = {}
    for label, directory in [("centred_reference", args.baseline), ("current016", args.strong_current)]:
        if directory and (directory / "run.json").exists():
            dst = validation / label
            dst.mkdir(exist_ok=True)
            for filename in ["run.json", "plans.json", "metrics.json", "manifest.json", "scene_evidence.json"]:
                shutil.copy2(directory / filename, dst / filename)
            extras[label] = read(directory / "metrics.json")
            if label == "current016":
                extras[label]["attitude_geometry_audit"] = audit_attitude(directory)
                (dst / "controls_sampled.json").write_text((directory / "controls.json").read_text())
    (validation / "review_summary.json").write_text(json.dumps(dict(
        navigation=read(args.suite / "summary.json"), geometry=audits, extras=extras,
        probe_checks=probe["checks"],
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [ROOT / "scripts/hydrodynamics.py", ROOT / "scripts/run_sim.py",
                                 ROOT / "config/experiments/hydro_coupled.json"]}), indent=2))
    print(json.dumps(audits, indent=2))


if __name__ == "__main__":
    main()
