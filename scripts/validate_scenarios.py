"""Check added-obstacle XY feasibility; excludes source-pool collision geometry.

This limited check cannot certify the actual navigation map or goal validity.
Use the runtime inflated map audit for those checks.
"""
from collections import deque
import json
import os
import runpy
import numpy as np
from pxr import Usd
from experiment import ROOT, load_experiment


def feasible_route(config, polygon):
    low = np.floor(polygon.min(axis=0)*10)/10
    high = np.ceil(polygon.max(axis=0)*10)/10
    xx, yy = np.meshgrid(np.arange(low[0], high[0]+.05, .1), np.arange(low[1], high[1]+.05, .1))
    points = np.column_stack([xx.ravel(), yy.ravel()])
    inside = np.zeros(len(points), dtype=bool)
    edge_distance = np.full(len(points), np.inf)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        inside ^= ((a[1] > points[:,1]) != (b[1] > points[:,1])) & (
            points[:,0] < (b[0]-a[0])*(points[:,1]-a[1])/(b[1]-a[1]+1e-20)+a[0])
        edge = b-a
        projection = np.clip(((points-a) @ edge)/(edge @ edge), 0, 1)
        edge_distance = np.minimum(edge_distance, np.linalg.norm(points-a-projection[:,None]*edge, axis=1))
    free = inside & (edge_distance > .4)
    for obj in config["obstacles"]:
        center, size = np.array(obj["position"][:2]), np.array(obj["size"][:2])
        if obj.get("type") == "cylinder":
            distance = np.linalg.norm(points-center, axis=1)-size[0]/2
        else:
            distance = np.linalg.norm(np.maximum(np.abs(points-center)-size/2, 0), axis=1)
        free &= distance > .55
    start, goal = [int(np.argmin(np.linalg.norm(points-np.array(config[key][:2]), axis=1))) for key in ("start", "goal")]
    assert free[start] and free[goal], "Start/goal violates inflated boundary"
    queue, parent = deque([start]), {start: None}
    width = xx.shape[1]
    while queue and goal not in parent:
        current = queue.popleft()
        row, col = divmod(current, width)
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = row+dr, col+dc
            if not (0 <= nr < xx.shape[0] and 0 <= nc < width):
                continue
            neighbor = nr*width+nc
            if free[neighbor] and neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)
    assert goal in parent, "No XY route with 0.55 m obstacle clearance"
    route, current = [], goal
    while current is not None:
        route.append(points[current].tolist())
        current = parent[current]
    return route[::-1]


if __name__ == "__main__":
    reports = []
    for name in json.loads((ROOT / "config/scenarios.json").read_text()):
        os.environ["ROV_SCENARIO"] = name
        runpy.run_path(str(ROOT / "scripts/validate_scene.py"))
        c = load_experiment(name)
        stage = Usd.Stage.Open(c["scene_file"])
        polygon = np.array(json.loads((ROOT / c["water_boundary"]).read_text()))
        route = feasible_route(c, polygon)
        reports.append({"scenario": name, "scene_checks": "passed", "obstacles": len(c["obstacles"]),
                        "feasibility_route_xy": route, "source_pool_geometry_checked": False, "note": "Added obstacles only; original pool colliders and runtime inflated occupancy are NOT covered."})
        print(name, "PASS:", len(c["obstacles"]), "added obstacles: route exists in this LIMITED check (source pool excluded)")
    (ROOT / "logs/scenario_validation.json").write_text(json.dumps(reports, indent=2))
