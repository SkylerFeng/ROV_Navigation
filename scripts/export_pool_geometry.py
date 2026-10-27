"""Export actual pool-mesh cross sections for honest XY route figures (USD Python)."""
import json
from pathlib import Path
import numpy as np
from pxr import Usd, UsdGeom
from experiment import ROOT, load_experiment


def export():
    stage = Usd.Stage.Open(load_experiment()["scene_file"])
    prim = stage.GetPrimAtPath('/World/Environment/Platform/Collision/Platform_collision_clean/mesh')
    mesh = UsdGeom.Mesh(prim)
    vertices = np.array(mesh.GetPointsAttr().Get())
    matrix = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
    vertices = (np.column_stack((vertices, np.ones(len(vertices)))) @ matrix)[:, :3]
    indices = np.array(mesh.GetFaceVertexIndicesAttr().Get())
    faces = []; offset = 0
    for count in mesh.GetFaceVertexCountsAttr().Get():
        for i in range(1, count-1):
            faces.append(indices[[offset, offset+i, offset+i+1]])
        offset += count
    triangles = vertices[np.array(faces)]
    segments = []
    # Envelope occupied by our collision hull when level at z=1.0.
    heights = [.986, 1.116, 1.246]
    for z in heights:
        subset = triangles[(triangles[:, :, 2].min(axis=1) < z) & (triangles[:, :, 2].max(axis=1) > z)]
        for tri in subset:
            points = []
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                if (a[2] < z) != (b[2] < z):
                    points.append((a + (b-a)*(z-a[2])/(b[2]-a[2]))[:2].tolist())
            if len(points) == 2 and all(-3.65 < p[0] < 4.35 and -2.15 < p[1] < 3.25 for p in points):
                segments.append(points)
    result = {'collider': str(prim.GetPath()), 'slice_heights_m': heights, 'segments': segments}
    output = ROOT / 'scenes/pool_collision_sections.json'
    output.write_text(json.dumps(result))
    print(f'{len(segments)} cross-section segments: {output}')


if __name__ == '__main__':
    export()
