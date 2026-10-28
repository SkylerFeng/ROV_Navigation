"""Check composed transforms, colliders, clearances, and source assets."""
import json
import os
from pathlib import Path
from pxr import Usd, UsdGeom, UsdPhysics
from experiment import load_experiment

root = Path(__file__).resolve().parents[1]
c = load_experiment()
s = Usd.Stage.Open(c["scene_file"])
assert s and s.GetDefaultPrim().GetPath() == "/World"
assert UsdGeom.GetStageMetersPerUnit(s) == 1
assert UsdGeom.GetStageUpAxis(s) == "Z"
assert s.GetPrimAtPath("/World/ROV").HasAPI(UsdPhysics.RigidBodyAPI)
assert s.GetPrimAtPath(c["collision_prim"]).HasAPI(UsdPhysics.CollisionAPI)
xf = UsdGeom.XformCache()
robot_pos = xf.GetLocalToWorldTransform(s.GetPrimAtPath("/World/ROV")).ExtractTranslation()
assert all(abs(a-b) < 1e-5 for a, b in zip(robot_pos, c["start"]))
translation = xf.GetLocalToWorldTransform(s.GetPrimAtPath("/World/Environment/Platform")).ExtractTranslation()
# Source assets may contain their own root translation (the old Platform does).
environment_translation = xf.GetLocalToWorldTransform(s.GetPrimAtPath("/World/Environment")).ExtractTranslation()
assert all(abs(a-b) < 1e-5 for a, b in zip(environment_translation, c["environment_offset"]))
for obstacle in c["obstacles"]:
    prim = s.GetPrimAtPath("/World/Obstacles/" + obstacle["name"])
    assert prim.HasAPI(UsdPhysics.CollisionAPI)
    assert not prim.HasAPI(UsdPhysics.RigidBodyAPI)
    assert abs(xf.GetLocalToWorldTransform(prim).ExtractTranslation()[2] - obstacle["position"][2]) < 1e-6
for position in [c["start"], c["goal"]]:
    assert position[2] - 0.014 > c["pool_floor"]
    assert position[2] + 0.246 < c["water_surface"]
    for obstacle in c["obstacles"]:
        assert any(abs(position[i]-obstacle["position"][i]) > obstacle["size"][i]/2 + [0.24, 0.285, 0.26][i] for i in range(3))
empty = [str(p) for p in Path(c["platform"]).parent.rglob("*.usd") if p.stat().st_size == 0]
report = {"scene_checks": "passed", "robot": "/World/ROV", "static_obstacles": len(c["obstacles"]),
          "source_to_world": list(translation), "empty_source_assets": empty,
          "limitation": "Static transform and added-obstacle checks only; source-mesh route clearance is not checked here."}
(root / f"logs/scene_validation_{c['scenario']}.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "empty_source_assets"}, indent=2))
