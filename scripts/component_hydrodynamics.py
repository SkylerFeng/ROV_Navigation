"""Geometry-based reduced-order surface drag, not a pressure/CFD solver.

Each compiled patch uses a two-sided dissipative normal law and tangential
friction. The global 0.5 paired-surface factor is explicit and uncalibrated.
Independent components ignore wake/shielding, including internal CAD surfaces.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class ComponentHydrodynamics:
    def __init__(self, settings):
        path = Path(settings['component_model_file'])
        self.path = path if path.is_absolute() else ROOT/path
        data = json.loads(self.path.read_text())
        if data.get('schema_version') != 1:
            raise ValueError('Unsupported component geometry schema')
        patches = data['patches']
        self.centers = np.asarray(patches['centers_body_m'], dtype=float)
        self.offsets = self.centers-np.asarray(settings['center_of_mass_body_m'])
        self.normals = np.asarray(patches['normals_body'], dtype=float)
        self.areas = np.asarray(patches['area_m2'], dtype=float)
        ids = np.asarray(patches['component_ids'], dtype=int)
        self.ids, self.index = np.unique(ids, return_inverse=True)
        self.count = len(self.ids)
        self.patch_count = len(self.areas)
        if (not self.patch_count or self.centers.shape != (self.patch_count, 3)
                or self.normals.shape != self.centers.shape or len(ids) != self.patch_count
                or not np.isfinite(self.centers).all() or not np.isfinite(self.normals).all()
                or not np.isfinite(self.areas).all() or np.any(self.areas <= 0)
                or not np.allclose(np.linalg.norm(self.normals, axis=1), 1., atol=1e-6)):
            raise ValueError('Invalid component surface geometry')
        self.p = settings
        self.width = float(data['cell_size_m'])
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def wrench(self, relative, angular, wet_fraction=None):
        p = self.p
        wet = np.ones(self.patch_count) if wet_fraction is None else np.asarray(wet_fraction)
        if wet.shape != (self.patch_count,) or not np.isfinite(wet).all() or np.any((wet < 0) | (wet > 1)):
            raise ValueError('Invalid patch wet fractions')
        local = np.asarray(relative)+np.cross(angular, self.offsets)
        normal_speed = np.einsum('ij,ij->i', local, self.normals)
        tangent = local-normal_speed[:, None]*self.normals
        normal_force = (p['component_normal_cd']*np.abs(normal_speed)*normal_speed)[:, None]*self.normals
        tangent_force = p['component_tangential_cf']*np.linalg.norm(tangent, axis=1)[:, None]*tangent
        forces = -.5*p['density_kg_m3']*p['component_surface_factor']*(self.areas*wet)[:, None]*(normal_force+tangent_force)
        torques = np.cross(self.offsets, forces)
        # Retain full geometry in configuration; bounded per-step telemetry.
        aggregate_f = np.column_stack([np.bincount(self.index, weights=forces[:, j], minlength=self.count) for j in range(3)])
        aggregate_t = np.column_stack([np.bincount(self.index, weights=torques[:, j], minlength=self.count) for j in range(3)])
        active = np.argsort(np.linalg.norm(aggregate_f, axis=1))[-8:][::-1]
        details = dict(component_count=self.count, patch_count=self.patch_count,
                       geometry_sha256=self.sha256,
                       wetted_area_m2=float(np.sum(self.areas*wet)),
                       relative_drag_power_w=float(np.sum(forces*local)),
                       component_drag_force_body_n=aggregate_f.sum(axis=0).tolist(),
                       component_drag_torque_body_nm=aggregate_t.sum(axis=0).tolist(),
                       strongest_components=[dict(id=int(self.ids[i]), force_body_n=aggregate_f[i].tolist(),
                                                torque_body_nm=aggregate_t[i].tolist()) for i in active])
        return forces.sum(axis=0), torques.sum(axis=0), details

    def wet_fractions(self, position, rotation, surface, bottom, boundary):
        # Patch-centroid quadrature with a cell-wide vertical transition.
        # This is wetted area only, never enclosed/displaced volume.
        from hydrodynamics import inside_polygon
        world = np.asarray(position)+self.centers @ rotation.T
        wet = np.clip((surface-world[:, 2])/self.width+.5, 0, 1)
        wet *= np.clip((world[:, 2]-bottom)/self.width+.5, 0, 1)
        # Vectorized ray casting; check every patch rather than COM only.
        inside = np.zeros(self.patch_count, dtype=bool)
        previous = boundary[-1]
        x, y = world[:, 0], world[:, 1]
        for point in boundary:
            x1, y1 = previous; x2, y2 = point
            if y1 != y2:
                inside ^= ((y1 > y) != (y2 > y)) & (x < (x2-x1)*(y-y1)/(y2-y1)+x1)
            previous = point
        return wet*inside
