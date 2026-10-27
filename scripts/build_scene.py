"""Compose an independent experiment without changing supplied USD assets."""
import argparse
import json
from pathlib import Path
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade
from experiment import load_experiment

ROOT = Path(__file__).resolve().parents[1]


def translate(prim, position):
    xform = UsdGeom.Xformable(prim)
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            op.Set(Gf.Vec3d(*position))
            return
    xform.AddTranslateOp().Set(Gf.Vec3d(*position))


def reveal_pool_collision(stage):
    # Supplied visual tiles are incomplete and the collision mesh is hidden.
    # Render the actual collider so ideal camera depth sees the same structures
    # that block the ROV; this is a local override, not an edit to source assets.
    collider = stage.GetPrimAtPath("/World/Environment/Platform/Collision/Platform_collision_clean/mesh")
    UsdGeom.Imageable(collider).MakeVisible()
    # Imported collision triangles have inconsistent winding. PhysX blocks
    # either side, so camera depth must also see either side of the proxy.
    UsdGeom.Mesh(collider).CreateDoubleSidedAttr(True)
    material = UsdShade.Material.Define(stage, "/World/PoolCollisionMaterial")
    shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("Surface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.38, .42, .45))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(.9)
    shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
    shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(collider).Bind(material)


def build(scenario, show_pool_collision=False):
    CONFIG = load_experiment(scenario)
    output = Path(CONFIG["scene_file"])
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(output))
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    outer = UsdGeom.Xform.Define(stage, "/World/Environment")
    translate(outer, CONFIG["environment_offset"])
    platform = UsdGeom.Xform.Define(stage, "/World/Environment/Platform")
    platform.GetPrim().GetReferences().AddReference(CONFIG["platform"])
    if show_pool_collision:
        reveal_pool_collision(stage)
    water = UsdGeom.Xform.Define(stage, "/World/Water")
    water.GetPrim().GetReferences().AddReference(CONFIG["water"])
    translate(water, CONFIG["source_to_world"])
    # Suppress the bright water specular highlight that obscures the overview.
    water_shader = UsdShade.Shader(stage.GetPrimAtPath("/World/Water/Looks/Water/PreviewSurface"))
    water_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(.85)
    water_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(.12)
    water_shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.0)
    water_shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
    water_shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0))
    # Water surface has no collider; run_sim supplies the configured fluid model.
    for obj in CONFIG["obstacles"]:
        path = "/World/Obstacles/" + obj["name"]
        if obj.get("type") == "cylinder":
            cube = UsdGeom.Cylinder.Define(stage, path)
            cube.CreateRadiusAttr(0.5)
            cube.CreateHeightAttr(1.0)
            cube.CreateAxisAttr("Z")
        else:
            cube = UsdGeom.Cube.Define(stage, path)
            cube.CreateSizeAttr(1.0)
        translate(cube, obj["position"])
        cube.AddScaleOp().Set(Gf.Vec3f(*obj["size"]))
        color = (0.12, 0.65, 0.85) if obj.get("type") == "cylinder" else (0.9, 0.28, 0.08)
        cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        material = UsdShade.Material.Define(stage, "/World/ObstacleMaterials/"+obj["name"])
        shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("Surface"))
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(.85)
        shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
        shader.CreateInput("specularColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0))
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(cube.GetPrim()).Bind(material)
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    for name, position, color in [("Start", CONFIG["start"], (0.1, 0.9, 0.2)),
                                  ("Goal", CONFIG["goal"], (0.1, 0.4, 1.0))]:
        marker = UsdGeom.Sphere.Define(stage, "/World/Markers/" + name)
        marker.CreateRadiusAttr(0.1)
        translate(marker, [position[0], position[1], CONFIG["water_surface"] + 0.1])
        marker.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    robot = UsdGeom.Xform.Define(stage, "/World/ROV")
    robot.GetPrim().GetReferences().AddReference(CONFIG["robot"])
    translate(robot, CONFIG["start"])
    UsdPhysics.RigidBodyAPI.Apply(robot.GetPrim())
    UsdPhysics.MassAPI.Apply(robot.GetPrim()).CreateMassAttr(5.0)
    # Explicit hull avoids treating the model's empty frame as a solid mesh.
    hull = UsdGeom.Cube.Define(stage, "/World/ROV/CollisionHull")
    hull.CreateSizeAttr(1.0)
    translate(hull, [0.0, 0.0, 0.116])
    hull.AddScaleOp().Set(Gf.Vec3f(0.48, 0.57, 0.26))
    hull.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    UsdPhysics.CollisionAPI.Apply(hull.GetPrim())
    physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    physics.CreateGravityMagnitudeAttr(0.0)
    stage.GetRootLayer().customLayerData = {"scenario": scenario, "title": CONFIG["title"]}
    stage.GetRootLayer().Save()
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--show-pool-collision", action="store_true", help="Diagnostic: render original hidden pool collider")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    selected = load_experiment(args.scenario)["scenario"]
    names = json.loads((ROOT / "config/scenarios.json").read_text()) if args.all else [selected]
    for name in names:
        build(name, args.show_pool_collision)
    # Preserve the editor's existing entry point as a composed active scene.
    alias = Usd.Stage.CreateNew(str(ROOT / "scenes/pool_navigation.usda"))
    alias.GetRootLayer().subLayerPaths = [f"pool_{selected}.usda"]
    alias.SetDefaultPrim(alias.GetPrimAtPath("/World"))
    alias.GetRootLayer().Save()
    (ROOT / "config/active_scenario.json").write_text(json.dumps({"scenario": selected}, indent=2))
