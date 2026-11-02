"""Audit composed HighBay geometry and conservative spawn clearance (USD Python)."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics, Sdf
from experiment import ROOT, load_experiment


def point_triangle_distance(point, triangles):
    """Exact point-to-triangle distances, including edge/vertex regions."""
    a, b, c = triangles.transpose(1, 0, 2)
    u, v, q = b-a, c-a, point-a
    uu, uv, vv = (np.einsum("ij,ij->i", x, y) for x, y in [(u,u), (u,v), (v,v)])
    qu, qv = (np.einsum("ij,ij->i", q, x) for x in [u,v])
    det = uu*vv-uv*uv
    valid = det > 1e-16
    safe = np.where(valid, det, 1)
    s, t = (qu*vv-qv*uv)/safe, (qv*uu-qu*uv)/safe
    inside = valid & (s >= 0) & (t >= 0) & (s+t <= 1)
    distances = np.where(inside, np.linalg.norm(q-s[:,None]*u-t[:,None]*v, axis=1), np.inf)
    for start, end in [(a,b), (b,c), (c,a)]:
        edge = end-start
        length2 = np.einsum("ij,ij->i", edge, edge)
        phase = np.clip(np.einsum("ij,ij->i", point-start, edge)/np.maximum(length2, 1e-20), 0, 1)
        distances = np.minimum(distances, np.linalg.norm(point-start-phase[:,None]*edge, axis=1))
    return distances


def world_points(prim):
    points = np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get())
    matrix = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
    return (np.c_[points, np.ones(len(points))] @ matrix)[:,:3], matrix


def audit(scenario):
    c = load_experiment(scenario)
    assert c["platform"].endswith("/HighBay/HighBay.usd"), "Expected original HighBay asset"
    stage = Usd.Stage.Open(c["scene_file"])
    prim = stage.GetPrimAtPath(c["collision_prim"])
    assert prim.HasAPI(UsdPhysics.CollisionAPI)
    assert UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() == "none"
    mesh = UsdGeom.Mesh(prim)
    vertices, matrix = world_points(prim)
    assert np.allclose(matrix[:3,:3], np.eye(3)), "HighBay must not be scaled or rotated"
    assert np.allclose(matrix[3,:3], c["environment_offset"])
    indices = np.array(mesh.GetFaceVertexIndicesAttr().Get())
    counts = np.array(mesh.GetFaceVertexCountsAttr().Get())
    assert np.all(counts == 3), "Audit expects triangulated collider"
    triangles = vertices[indices.reshape(-1,3)]
    hull = c["hydrodynamics"]["hull_size_m"]
    radius = float(np.linalg.norm(hull)/2)
    clearance = {}
    for name in ["start", "goal"]:
        center = np.array(c[name])+c["hydrodynamics"]["center_of_mass_body_m"]
        distance = float(point_triangle_distance(center, triangles).min())
        clearance[name] = distance-radius
        assert clearance[name] > .05, f"Unsafe {name}: sphere clearance {clearance[name]:.3f} m"
    water = stage.GetPrimAtPath("/World/Water")
    assert not any(p.HasAPI(UsdPhysics.CollisionAPI) for p in Usd.PrimRange(water))
    surfaces = [p for p in Usd.PrimRange(water) if p.IsA(UsdGeom.Mesh)]
    assert len(surfaces) == 1
    points, _ = world_points(surfaces[0])
    boundary = np.array(json.loads((ROOT/c["water_boundary"]).read_text()))
    assert np.allclose(points[:,2], c["water_surface"])
    assert np.allclose(points[:,:2], boundary)
    assert c["pool_floor"] < c["start"][2]-.02
    assert c["water_surface"] > c["start"][2]+.25
    missing = []
    assets = set()
    for p in stage.Traverse():
        # Isaac resolves the ROV's built-in MDL modules at runtime. This
        # standalone USD audit checks HighBay and the configured water assets.
        if not str(p.GetPath()).startswith(("/World/Environment/", "/World/Water/")):
            continue
        for attr in p.GetAttributes():
            if attr.GetTypeName() == Sdf.ValueTypeNames.Asset:
                value = attr.Get()
                if value and value.path:
                    if not value.resolvedPath: missing.append(str(attr.GetPath()))
                    else: assets.add(value.resolvedPath)
    assert not missing, f"Unresolved environment/water assets: {missing[:5]}"
    layers = {layer.realPath for layer in stage.GetUsedLayers() if layer.realPath}
    files = sorted(assets | layers)
    hashes = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in files}
    return dict(scenario=scenario, passed=True, source_asset=c["platform"],
                source_to_world_translation=c["environment_offset"], source_scale=[1,1,1],
                collision_points=len(vertices), collision_triangles=len(triangles),
                visual_meshes=sum(p.IsA(UsdGeom.Mesh) and "/Visual/" in str(p.GetPath()) for p in stage.Traverse()),
                unresolved_assets=missing, asset_sha256=hashes,
                conservative_endpoint_sphere_clearance_m=clearance,
                water_boundary=boundary.tolist(), water_surface=c["water_surface"],
                note="Configured test region, not a measured HighBay water level. Endpoint clearance does not certify the route.")


def audit_run(directory):
    """Conservative sphere-to-scan distance at recorded samples, not a sweep."""
    run = json.loads((directory/"run.json").read_text())
    c = run["config"]
    snapshot = directory/"sources/scenes"/Path(c["scene_file"]).name
    stage = Usd.Stage.Open(str(snapshot))
    prim = stage.GetPrimAtPath(c["collision_prim"])
    vertices, _ = world_points(prim)
    mesh = UsdGeom.Mesh(prim)
    assert all(n == 3 for n in mesh.GetFaceVertexCountsAttr().Get())
    triangles = vertices[np.array(mesh.GetFaceVertexIndicesAttr().Get()).reshape(-1,3)]
    from scipy.spatial import cKDTree
    tree = cKDTree(vertices)
    low, high = triangles.min(axis=1), triangles.max(axis=1)
    radius = np.linalg.norm(c["hydrodynamics"]["hull_size_m"])/2
    samples = np.array(run["samples"])
    # The sphere is centred on the hull/COM, including the measured attitude.
    from hydrodynamics import rotation_matrix, inside_polygon
    controls = json.loads((directory/"controls.json").read_text())
    assert len(controls) == len(samples)
    rotations = np.array([rotation_matrix(row["orientation"]) for row in controls])
    centers = samples[:,1:4]+np.array([rotation_matrix(row["orientation"]) @
                c["hydrodynamics"]["center_of_mass_body_m"] for row in controls])
    clearances = []
    for center in centers:
        upper, _ = tree.query(center)
        box_delta = np.maximum(np.maximum(low-center, center-high), 0)
        possible = np.einsum("ij,ij->i", box_delta, box_delta) <= (upper+1e-8)**2
        clearances.append(float(point_triangle_distance(center, triangles[possible]).min()-radius))
    boundary = np.array(json.loads((directory/"sources"/c["water_boundary"]).read_text()))
    # The configured water region is convex, so checking every oriented hull
    # corner establishes footprint containment at each sampled attitude.
    from itertools import product
    corners_body = np.array(list(product([-.5,.5], repeat=3)))*c["hydrodynamics"]["hull_size_m"]
    corners = centers[:,None,:]+np.einsum("nij,kj->nki", rotations, corners_body)
    corner_xy = corners[:,:,:2].reshape(-1,2)
    boundary_clearance = np.full(len(corner_xy), np.inf)
    for a, b in zip(boundary, np.roll(boundary,-1,axis=0)):
        edge = b-a
        phase = np.clip((corner_xy-a) @ edge/(edge @ edge), 0, 1)
        boundary_clearance = np.minimum(boundary_clearance, np.linalg.norm(corner_xy-a-phase[:,None]*edge,axis=1))
    inside = all(inside_polygon(p[:2], boundary) for p in centers)
    corner_inside = np.array([inside_polygon(p, boundary) for p in corner_xy])
    boundary_clearance = np.where(corner_inside, boundary_clearance, -boundary_clearance)
    corners_inside = bool(corner_inside.all())
    return dict(scenario=run["scenario"], samples=len(samples),
                sample_max_interval_s=float(np.diff(samples[:,0]).max()),
                minimum_scanned_mesh_sphere_clearance_m=min(clearances),
                minimum_water_boundary_hull_corner_clearance_m=float(boundary_clearance.min()),
                all_sampled_hull_centers_inside_water=inside,
                all_sampled_hull_corners_inside_water=corners_inside,
                no_contact_events=not run["contacts"],
                passed=min(clearances)>0 and corners_inside and inside and not run["contacts"],
                note="Conservative circumscribed hull sphere at recorded samples; not continuous swept collision certification. Artificial obstacles are assessed separately.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="highbay")
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_run(args.run_directory.resolve()) if args.run_directory else audit(args.scenario)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "asset_sha256"}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
