"""Compile the supplied merged USD mesh into traceable wetted-surface patches.

Run with scripts/usd_python.sh. Geometry is measured; drag coefficients are not.
No source asset or scene is modified. scipy is required only for this exporter.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pxr import Usd, UsdGeom

ROOT = Path(__file__).resolve().parents[1]


def compile_mesh(asset, mesh_path, cell_m=.04):
    stage = Usd.Stage.Open(str(asset))
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(mesh_path))
    if not mesh:
        raise ValueError('Expected an explicit Mesh prim')
    points = np.asarray(mesh.GetPointsAttr().Get(), dtype=float)
    matrix = np.array(UsdGeom.XformCache().GetLocalToWorldTransform(mesh.GetPrim()))
    # Gf matrices use row vectors. This includes all nested asset transforms.
    points = points @ matrix[:3, :3] + matrix[3, :3]
    points *= UsdGeom.GetStageMetersPerUnit(stage)
    if UsdGeom.GetStageUpAxis(stage) != 'Z':
        raise ValueError('Only the actual Z-up asset is supported; do not silently rotate')
    counts = np.asarray(mesh.GetFaceVertexCountsAttr().Get())
    if not np.all(counts == 3):
        raise ValueError('Triangulate source explicitly before exporting')
    faces = np.asarray(mesh.GetFaceVertexIndicesAttr().Get()).reshape(-1, 3)
    # Weld only for connectivity, not to alter area/positions. 10 micrometres.
    _, welded = np.unique(np.round(points / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    indices = welded[faces]
    a = np.concatenate([indices[:, 0], indices[:, 1], indices[:, 2]])
    b = np.concatenate([indices[:, 1], indices[:, 2], indices[:, 0]])
    graph = coo_matrix((np.ones(len(a), dtype=bool), (a, b)), shape=(welded.max()+1,)*2).tocsr()
    _, labels = connected_components(graph, directed=False)
    triangle_labels = labels[indices[:, 0]]
    tri = points[faces]
    cross = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    area = np.linalg.norm(cross, axis=1)/2
    valid = area > 1e-12
    centroids = tri.mean(axis=1)[valid]
    normals = cross[valid]/(2*area[valid, None])
    areas = area[valid]
    shells = triangle_labels[valid]
    # Two-sided cross-flow patches: n and -n have identical force laws.
    dominant = np.argmax(np.abs(normals), axis=1)
    sign = np.where(normals[np.arange(len(normals)), dominant] < 0, -1., 1.)
    normals *= sign[:, None]
    keys = np.column_stack([shells, np.floor(centroids/cell_m).astype(int),
                            dominant])
    unique, inverse = np.unique(keys, axis=0, return_inverse=True)
    n = len(unique)
    total_area = np.bincount(inverse, weights=areas, minlength=n)
    centers = np.column_stack([np.bincount(inverse, weights=areas*centroids[:, j], minlength=n)/total_area for j in range(3)])
    means = np.column_stack([np.bincount(inverse, weights=areas*normals[:, j], minlength=n) for j in range(3)])
    means /= np.linalg.norm(means, axis=1)[:, None]
    components = []
    for label in np.unique(shells):
        mask = shells == label
        vertices = points[np.unique(faces[valid][mask])]
        components.append(dict(id=int(label), name=f'mesh_shell_{label:04d}',
                               triangle_count=int(mask.sum()), area_m2=float(areas[mask].sum()),
                               min_body_m=vertices.min(axis=0).tolist(), max_body_m=vertices.max(axis=0).tolist()))
    return dict(schema_version=1, source_asset=str(asset.resolve()), source_mesh=mesh_path,
                source_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
                geometry_frame='body origin, metres, Z-up; runtime subtracts configured centre of mass',
                method='Welded geometric connectivity; area-weighted centroid/normal patches. Names are geometric IDs, not semantic part labels.',
                limits='No shielding, wake, pressure solve or automatic sealed-volume identification. Two-sided surface law approximates paired surfaces with a 0.5 area factor.',
                cell_size_m=cell_m, source_triangle_count=len(faces), degenerate_triangles=int((~valid).sum()),
                bounds_body_m=[points.min(axis=0).tolist(), points.max(axis=0).tolist()],
                components=components, patches=dict(component_ids=unique[:, 0].tolist(),
                   centers_body_m=centers.tolist(), normals_body=means.tolist(), area_m2=total_area.tolist()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=Path, default=Path('/home/ache/OceanSim_assets/Bluerov/BROV_low.usd'))
    parser.add_argument('--mesh', default='/BlueROV/Mesh/Mesh')
    parser.add_argument('--output', type=Path, default=ROOT/'config/hydrodynamic_components/bluerov_mesh.json')
    parser.add_argument('--cell-size', type=float, default=.04)
    args = parser.parse_args()
    if not np.isfinite(args.cell_size) or args.cell_size <= 0:
        raise ValueError('cell-size must be positive')
    data = compile_mesh(args.asset, args.mesh, args.cell_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, separators=(',', ':'))+chr(10))
    print(json.dumps(dict(components=len(data['components']), patches=len(data['patches']['area_m2']),
                         area_m2=sum(data['patches']['area_m2']), bounds=data['bounds_body_m'], output=str(args.output))))


if __name__ == '__main__':
    main()
