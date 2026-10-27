"""Run isolated, repeatable scenario tests and preserve failures as results."""
import argparse
import csv
import hashlib
import shutil
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from experiment import ROOT, load_experiment


def stop(process):
    if process.poll() is None:
        # ros2 launch forwards SIGINT to children; signaling the whole group
        # would interrupt each child twice, including during node cleanup.
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_case(name, directory, limit, domain, sim_limit=180, tolerance=.01, settle=2, cloud_stride=1, scene_directory=None, gui=False, goal_delay=0):
    c = load_experiment(name)
    if scene_directory:
        c["scene_file"] = str((scene_directory / f"pool_{name}.usda").resolve())
    if not Path(c["scene_file"]).exists():
        raise RuntimeError("Build scenes first: bash scripts/usd_python.sh scripts/build_scene.py --all")
    if (directory / "run.json").exists():
        raise FileExistsError(f"Existing results at {directory}; choose a fresh --output-dir")
    directory.mkdir(parents=True, exist_ok=True)
    geometry = ROOT / "scenes/pool_collision_sections.json"
    if geometry.exists():
        shutil.copy2(geometry, directory / "pool_collision_sections.json")
    source_dir = directory / "sources"
    source_dir.mkdir(exist_ok=True)
    sources = sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "config").glob("*.json")) + [Path(c["scene_file"])]
    sources += sorted((ROOT / "ros_ws/src/plan_manage/src").glob("*.cpp"))
    sources += sorted((ROOT / "ros_ws/src/plan_manage/include").rglob("*.h"))
    if c.get("overrides_file"):
        sources.append(Path(c["overrides_file"]))
    manifest = {}
    for source in sources:
        try:
            relative = source.relative_to(ROOT)
        except ValueError:
            relative = Path("external_overrides") / source.name
        destination = source_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
    def git_output(*arguments):
        result = subprocess.run(["git", "-C", str(ROOT), *arguments], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    (directory / "manifest.json").write_text(json.dumps({"sha256": manifest,
        "git_commit": git_output("rev-parse", "HEAD"),
        "git_status": git_output("status", "--porcelain"), "config": c,
        "ROS_DOMAIN_ID": domain, "wall_time_limit": limit, "sim_time_limit": sim_limit,
        "arrival_tolerance": tolerance, "settle_time": settle, "cloud_stride": cloud_stride, "headless": not gui,
        "goal_delay_sim_seconds": goal_delay}, indent=2))
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), ROV_SCENARIO=name, RMW_IMPLEMENTATION="rmw_fastrtps_cpp")
    children = []
    with (directory / "navigation.log").open("w") as nav_log, (directory / "simulation.log").open("w") as sim_log, (directory / "goal.log").open("w") as goal_log:
        try:
            nav = subprocess.Popen(["bash", str(ROOT / "scripts/start_navigation.sh")], env=env,
                stdout=nav_log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(nav)
            sim = subprocess.Popen(["bash", str(ROOT / "scripts/start_sim.sh"), *([] if gui else ["--headless"]), "--steps", "0",
                "--scenario", name, "--scene-file", c["scene_file"], "--cloud-stride", str(cloud_stride), "--sim-time-limit", str(sim_limit), "--arrival-tolerance", str(tolerance), "--settle-time", str(settle),
                "--wall-time-limit", str(limit), "--stop-on-goal", "--stop-on-blocked-goal", "--capture", "--top-view", "--output-dir", str(directory)],
                env=env, stdout=sim_log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(sim)
            sender = subprocess.Popen(["bash", str(ROOT / "scripts/send_goal.sh"), "--delay-sim-seconds", str(goal_delay)], env=env,
                stdout=goal_log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(sender)
            sim.wait(timeout=limit+150)
        except subprocess.TimeoutExpired:
            return {"scenario": name, "status": "startup_or_run_timeout", "goal_reached": False}
        finally:
            for process in reversed(children):
                stop(process)
    if not (directory / "run.json").exists():
        return {"scenario": name, "status": "runtime_error", "goal_reached": False}
    from export_run import export
    result = export(directory)
    result["status"] = "reached" if result["goal_reached"] else "not_reached"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", nargs="+", default=["baseline", "slalom", "gates", "pillars", "mixed"])
    parser.add_argument("--wall-time-limit", type=float, default=650)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--goal-delay", type=float, default=0, help="Wait this many simulation seconds after readiness before sending goal")
    parser.add_argument("--scene-directory", type=Path)
    parser.add_argument("--cloud-stride", type=int, choices=(1, 2, 4, 8), default=1)
    parser.add_argument("--sim-time-limit", type=float, default=180)
    parser.add_argument("--arrival-tolerance", type=float, default=.01)
    parser.add_argument("--settle-time", type=float, default=2)
    parser.add_argument("--domain", type=int, default=89)
    parser.add_argument("--output-dir", default=str(ROOT / "logs/suites" / time.strftime("%Y%m%d_%H%M%S")))
    args = parser.parse_args()
    if args.overrides:
        os.environ["ROV_EXPERIMENT_OVERRIDES"] = str(args.overrides.resolve())
    directory = Path(args.output_dir).resolve();directory.mkdir(parents=True, exist_ok=True)
    summary_file = directory / "summary.json"
    results = json.loads(summary_file.read_text()) if summary_file.exists() else []
    for name in args.scenarios:
        print("Testing", name, flush=True)
        result = run_case(name, directory / name, args.wall_time_limit, args.domain, args.sim_time_limit, args.arrival_tolerance, args.settle_time, args.cloud_stride, args.scene_directory, args.gui, args.goal_delay)
        results.append(result)
        (directory / "summary.json").write_text(json.dumps(results, indent=2))
        keys = sorted(set().union(*(r.keys() for r in results)))
        with (directory / "summary.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=keys);writer.writeheader();writer.writerows(results)
        print(json.dumps(result), flush=True)
