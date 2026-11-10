"""Clean engineering pool using the supplied Tile3 water footprint, not scan debris.

The water coordinates are interpreted explicitly as metres, Z-up (as authored
by build_tile3_water.py); source stage metadata is not used to rescale them.
"""
import json
import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, UsdLux
from experiment import ROOT


def material(stage, name, color, roughness=.65):
    mat = UsdShade.Material.Define(stage, '/World/Materials/'+name)
    shader = UsdShade.Shader.Define(stage, mat.GetPath().AppendChild('Surface'))
    shader.CreateIdAttr('UsdPreviewSurface')
    shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(roughness)
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
    return mat


def build_pool(stage, config):
    source = Usd.Stage.Open(config['water'])
    root = source.GetDefaultPrim()
    raw = np.asarray(root.GetAttribute('oceansim:water:boundaryXY').Get(), dtype=float)
    offset = np.asarray(config['source_to_world'], dtype=float)
    polygon = raw + offset[:2]
    bottom = float(root.GetAttribute('oceansim:water:bottomZ').Get()) + offset[2]
    surface = float(root.GetAttribute('oceansim:water:surfaceZ').Get()) + offset[2]
    if abs(bottom-config['pool_floor']) > 1e-6 or abs(surface-config['water_surface']) > 1e-6:
        raise ValueError('Pool heights must match transformed source water metadata')
    (ROOT/config['water_boundary']).write_text(json.dumps(polygon.tolist(), indent=2)+'\n')
    UsdGeom.Xform.Define(stage, '/World/Environment/Platform')
    mesh = UsdGeom.Mesh.Define(stage, config['collision_prim'])
    # Floor reuses the triangulated water surface, so both share the same edge.
    src = UsdGeom.Mesh(source.GetPrimAtPath(str(root.GetPath())+'/Surface'))
    points = np.asarray(src.GetPointsAttr().Get(), dtype=float) + offset
    points[:, 2] = bottom
    counts = list(src.GetFaceVertexCountsAttr().Get())
    indices = list(src.GetFaceVertexIndicesAttr().Get())
    # Vertical walls and a narrow coping strip. Both are outside the water
    # polygon, and physically collide; no hidden scan geometry remains.
    area = np.sum(polygon[:, 0]*np.roll(polygon[:, 1], -1)-polygon[:, 1]*np.roll(polygon[:, 0], -1))
    vertices = points.tolist()
    edges = np.roll(polygon, -1, axis=0)-polygon
    normals = np.column_stack((edges[:,1], -edges[:,0])) / np.linalg.norm(edges, axis=1)[:,None]
    normals *= 1 if area > 0 else -1
    previous = np.roll(normals, 1, axis=0)
    outer = polygon + .22*(normals+previous)/(1+np.sum(normals*previous,axis=1))[:,None]
    for i, (a, b) in enumerate(zip(polygon, np.roll(polygon, -1, axis=0))):
        top = surface+.16
        # Closed wall prism. Inner face is exactly the configured pool edge.
        quad = [a, b, outer[(i+1)%len(outer)], outer[i]]
        base = len(vertices)
        vertices.extend([[float(p[0]), float(p[1]), z] for z in (bottom-.15, top) for p in quad])
        for face in ((0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7), (4,5,6,7), (3,2,1,0)):
            counts.append(4); indices.extend(base+i for i in face)
    mesh.CreatePointsAttr(vertices)
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateDoubleSidedAttr(True)
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('none')
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material(stage, 'PoolCeramic', (.40,.64,.68)))
    # Neutral exterior ground is lower than the floor and has no scan fragments.
    ground = UsdGeom.Cube.Define(stage, '/World/Deck')
    ground.CreateSizeAttr(1)
    ground.AddTranslateOp().Set(Gf.Vec3d(0,0,bottom-.25))
    ground.AddScaleOp().Set(Gf.Vec3f(22,16,.18))
    UsdShade.MaterialBindingAPI.Apply(ground.GetPrim()).Bind(material(stage, 'Deck', (.15,.19,.23)))
    dome = UsdLux.DomeLight.Define(stage, '/World/Lighting/Dome')
    dome.CreateIntensityAttr(650)
    sun = UsdLux.DistantLight.Define(stage, '/World/Lighting/Key')
    sun.CreateIntensityAttr(1800)
    sun.CreateAngleAttr(12)
    sun.AddRotateXYZOp().Set(Gf.Vec3f(-25,-35,20))
    camera = UsdGeom.Camera.Define(stage, '/World/Overview')
    camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(10,-13,14), Gf.Vec3d(0,0,1), Gf.Vec3d(0,0,1)).GetInverse())
    camera.CreateClippingRangeAttr(Gf.Vec2f(.1,100))
    stage.GetRootLayer().customLayerData = {'geometry_kind':'engineered pool from Tile3 water footprint; not reconstructed pool walls', 'water_source':config['water']}
