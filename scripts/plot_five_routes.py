"""Presentation route figures with explicit measured-run provenance."""
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle, Circle, Patch

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "baseline": "Baseline", "slalom": "Slalom", "gates": "Offset gates",
    "pillars": "Pillar array", "mixed": "Mixed obstacles",
    "gates_clearance": "Gates (clearance corrected)",
}
COLORS = {"path": "green", "obstacle": "tomato", "goal": "blue", "end": "#ce7900"}


def load_case(suite, name):
    run = json.loads((suite / name / "run.json").read_text())
    geometry = suite / name / "pool_collision_sections.json"
    if geometry.exists():
        run["pool_sections"] = json.loads(geometry.read_text())["segments"]
    points = np.array(run["samples"], dtype=float)[:, 1:3]
    assert len(points) > 1 and np.isfinite(points).all()
    final = np.array(run["final_position"][:2], dtype=float)
    if not np.allclose(points[-1], final, atol=1e-8):
        points = np.vstack([points, final])
    config = run["config"]
    assert np.linalg.norm(points[0]-np.array(config["start"][:2])) < .1
    goal_error = float(np.linalg.norm(np.array(run["final_position"])-np.array(config["goal"])))
    assert abs(goal_error-run["goal_distance"]) < 1e-6
    return run, points, (run["stop_reason"] == "goal_reached" if "arrival_tolerance" in run else goal_error < config.get("goal_tolerance", .3))


def draw_case(ax, name, run, points, reached, compact=False, bounds=None):
    c = run["config"]
    if run.get("pool_sections"):
        ax.add_collection(LineCollection(run["pool_sections"], colors="#626b73", linewidths=1.1,
                                         zorder=2, label="Original pool structures"))
    for obj in c["obstacles"]:
        x, y = obj["position"][:2]
        sx, sy = obj["size"][:2]
        if obj.get("type") == "cylinder":
            patch = Circle((x, y), sx/2, facecolor=COLORS["obstacle"], zorder=2)
        else:
            patch = Rectangle((x-sx/2, y-sy/2), sx, sy, facecolor=COLORS["obstacle"], zorder=2)
        ax.add_patch(patch)
        label = obj["name"]
        ax.text(x, y, label, ha="center", va="center", fontsize=6.5 if compact else 10,
                zorder=3, color="black")
    ax.plot(points[:,0], points[:,1], color=COLORS["path"], lw=2.4 if compact else 2.8,
            label="Executed ROV path", zorder=4)
    ax.scatter(*c["start"][:2], s=35 if compact else 65, c=COLORS["path"], label="Start", zorder=6)
    ax.scatter(*c["goal"][:2], s=130 if compact else 230, c=COLORS["goal"], marker="*", label="Goal", zorder=6)
    if not reached:
        ax.scatter(*points[-1], s=65 if compact else 120, c=COLORS["end"], marker="X",
                   edgecolors="white", linewidths=.8, label="Final position (not reached)", zorder=7)
    tolerance = run.get("arrival_tolerance", c.get("goal_tolerance", .3))
    state = f"Reached (< {tolerance:.2f} m)" if reached else "Not reached within run budget"
    if not reached and run["stop_reason"] == "goal_occupied":
        state = "Stopped: goal occupied in inflated map"
    ax.text(.025, .965, state, transform=ax.transAxes, va="top",
            fontsize=10 if compact else 13, color="#27632a" if reached else "#986000",
            bbox={"facecolor":"white", "edgecolor":"#dddddd", "alpha":.94, "pad":5})
    title = f"ROV pool {name} | final goal error: {run['goal_distance']:.4f} m"
    ax.set_title(title if not compact else f"{NAMES[name]} | goal error: {run['goal_distance']:.4f} m",
                 fontsize=11 if compact else 20, pad=13)
    ax.set(xlim=(-3.65, 4.35), ylim=(-2.15, 3.25), xlabel="World X (m)", ylabel="World Y (m)")
    if bounds is not None:
        ax.set(xlim=bounds[:2], ylim=bounds[2:])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(np.arange(-3, 5, 1))
    ax.set_yticks(np.arange(-2, 3.5, .5))
    ax.grid(color="#bcbcbc", alpha=.45, linewidth=.8)
    ax.tick_params(labelsize=9 if compact else 13)
    ax.xaxis.label.set_size(10 if compact else 16)
    ax.yaxis.label.set_size(10 if compact else 16)
    if not compact:
        ax.legend(loc="lower right", fontsize=12, framealpha=.97)


def save_formats(fig, base, dpi):
    for extension in ("png", "pdf", "svg"):
        fig.savefig(base.with_suffix("."+extension), dpi=dpi, facecolor="white")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=ROOT / "logs/scenario_tests/recheck_20261014_diagnostic")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/figures/recheck_20261014")
    parser.add_argument("--scenarios", nargs=5, choices=NAMES,
                        default=["baseline", "slalom", "gates", "pillars", "mixed"])
    parser.add_argument("--case-map", type=json.loads, default={},
                        help='Display-to-recorded case mapping, e.g. {"gates":"gates_clearance"}')
    args = parser.parse_args()
    if len(set(args.scenarios)) != 5:
        parser.error("Choose five distinct scenarios")
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "svg.fonttype":"none", "pdf.fonttype":42})
    source_names = {name: args.case_map.get(name, name) for name in args.scenarios}
    cases = {name: load_case(args.suite, source_names[name]) for name in args.scenarios}
    all_points = np.vstack([points for _, points, _ in cases.values()])
    obstacle_corners = []
    for run, _, _ in cases.values():
        for obj in run["config"]["obstacles"]:
            center, half = np.array(obj["position"][:2]), np.array(obj["size"][:2])/2
            obstacle_corners.extend([center-half, center+half])
    all_points = np.vstack([all_points, obstacle_corners])
    bounds = (min(-3.65, all_points[:, 0].min()-.3), max(4.35, all_points[:, 0].max()+.3),
              min(-2.15, all_points[:, 1].min()-.3), max(3.25, all_points[:, 1].max()+.3))
    for name, (run, points, reached) in cases.items():
        fig, ax = plt.subplots(figsize=(16, 9))
        draw_case(ax, name, run, points, reached, bounds=bounds)
        fig.tight_layout(pad=1.5)
        save_formats(fig, args.output / f"route_{name}", 240)
        plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    for ax, (name, (run, points, reached)) in zip(axes.flat, cases.items()):
        draw_case(ax, name, run, points, reached, compact=True, bounds=bounds)
    ax = axes.flat[-1]
    ax.axis("off")
    handles = [
        Line2D([0],[0], color="green", lw=2.5, label="Executed ROV path"),
        Line2D([0],[0], marker="o", linestyle="", color="green", label="Start"),
        Line2D([0],[0], marker="*", linestyle="", markersize=13, color="blue", label="Goal"),
        Patch(facecolor="tomato", label="Added obstacle footprint"),
        Line2D([0],[0], color="#626b73", label="Original pool structures"),
        Line2D([0],[0], marker="X", linestyle="", color=COLORS["end"], label="Final position: not reached"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=13, frameon=False)
    first = next(iter(cases.values()))[0]
    tolerance = first.get("arrival_tolerance", first["config"].get("goal_tolerance", .3))
    budget = (f"Simulation budget: {first['sim_time_limit']:g} s per scenario" if first.get("sim_time_limit")
              else f"Wall-time budget: {first.get('wall_time_limit', 150):g} s per scenario")
    gate_note = "\nGates: corrected opening clearance" if "gates_clearance" in cases else ""
    ax.text(.03, .39, f"Measured navigation trajectories\nStart: {first['config']['start']} m\nGoal: {first['config']['goal']} m\nFixed reference height: z = 1.0 m\nHFOV: {first['config'].get('camera_horizontal_fov_deg', 53.03184):g} deg; depth stride: {first.get('cloud_stride', 4)}\nIdeal depth + ground-truth odometry\nArrival tolerance: {tolerance:g} m; dwell: {first.get('settle_time', 0):g} s\n{budget}{gate_note}\n\nRoutes are plotted without smoothing\nor extending them to the goal.",
            transform=ax.transAxes, va="top", fontsize=12, linespacing=1.45)
    fig.suptitle("ROV obstacle-avoidance routes across five pool scenarios", fontsize=20, y=.99)
    fig.tight_layout(rect=(0, 0, 1, .965), h_pad=3, w_pad=2)
    save_formats(fig, args.output / "five_routes_overview", 220)
    plt.close(fig)
    summary = []
    for name, (run, points, reached) in cases.items():
        summary.append({"scenario":name, "goal_error_m":run["goal_distance"], "goal_reached":reached,
                        "arrival_tolerance_m":run.get("arrival_tolerance", run["config"].get("goal_tolerance", .3)),
                        "settle_time_s":run.get("settle_time", 0), "stop_reason":run["stop_reason"],
                        "simulation_seconds":run.get("simulation_seconds", run["samples"][-1][0]),
                        "scene_file":run["config"]["scene_file"],
                        "samples_plotted":len(points), "obstacles":len(run["config"]["obstacles"]),
                        "recorded_scenario":run["scenario"],
                        "source":str(args.suite / source_names[name] / "run.json")})
    (args.output / "sources.json").write_text(json.dumps(summary, indent=2))
    lines = ["# 五种场景实测路线图", "", "与参考图使用相同的绿色实际轨迹、红色障碍、绿色起点、蓝色目标样式。",
             "", f"数据批次：{args.suite}。到达阈值 {tolerance:g} m，连续保持 {first.get('settle_time', 0):g} 秒。",
             f"本批起点：{first['config']['start']} m；目标：{first['config']['goal']} m。",
             f"相机水平视场 {first['config'].get('camera_horizontal_fov_deg',53.03184):g}°，深度采样步长 {first.get('cloud_stride',4)}。",
             "未做轨迹平滑或延伸到目标。未到达案例保留真实终止位置，并标出橙色 X。",
             "所有图使用相同坐标范围与 XY 等比例，便于比较。圆形表示立柱，矩形表示箱体/墙段。",
             "灰色细线表示原水池碰撞网格在 ROV 船体高度范围内的截面；与新增红色障碍一并显示。",
             "", "PNG 为 3840×2160，可直接用于 PPT；SVG/PDF 为矢量版本。", "", "| 场景 | 最终误差(m) | 本轮完成到达判定 | 图片 |", "|---|---:|---|---|"]
    if "gates_clearance" in cases:
        lines[4:4] = ["本轮门洞采用 gates_clearance：Gate2North 下端由 y=1.3 m 提高至 1.8 m，保留 0.5 m XY 障碍膨胀。该结果不代表原 gates 布局通过。", ""]
    if args.case_map:
        lines[4:4] = [f"场景数据目录映射：{args.case_map}。映射只选择原始实测数据，不改写日志或轨迹点；各场原始名称与完整来源见 sources.json。", ""]
    for row in summary:
        name = row["scenario"]
        lines.append(f"| {name} | {row['goal_error_m']:.4f} | {'是' if row['goal_reached'] else '否'} | [PNG](route_{name}.png) · [SVG](route_{name}.svg) · [PDF](route_{name}.pdf) |")
    lines += ["", "[五场景汇总图](five_routes_overview.png)", "", "数据来源见 sources.json。本轮为理想深度、真值位姿、固定高度实验，各场景一组起终点；不代表统计成功率。"]
    (args.output / "README.md").write_text("\n".join(lines)+"\n")
    archive = args.output.parent / (args.output.name + "_figures.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        for path in sorted(args.output.iterdir()):
            if path.is_file():
                stream.write(path, arcname=f"five_routes/{path.name}")
    print(json.dumps({"output":str(args.output), "archive":str(archive), "cases":summary}, indent=2))


if __name__ == "__main__":
    main()
