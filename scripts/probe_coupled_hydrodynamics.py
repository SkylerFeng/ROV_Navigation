"""Real PhysX acceleration/braking ablations; synthetic parameters, no pose animation."""
import argparse, json
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
from isaacsim import SimulationApp
app = SimulationApp({'headless': True})
try:
    import math, numpy as np
    from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleRigidPrim
    from hydrodynamics import Hydrodynamics, VelocityController, rotation_matrix
    root = Path(__file__).resolve().parents[1]
    coupled = json.loads((root / 'config/experiments/hydro_coupled.json').read_text())['hydrodynamics']
    variants = {
        'centred_baseline': {},
        'coupled_acceleration': coupled,
        'no_added_mass': {**coupled, 'added_mass_kg': [0]*3, 'added_inertia_kg_m2': [0]*3},
        'passive_tilt': coupled,
        'sway_stop': coupled,
        'level_brake': coupled,
        'level_brake_reverse': {**coupled, 'thrust_offset_body_m': [0, 0, -.045]},
        'level_brake_centred': {},
    }
    world = World(stage_units_in_meters=1.0, physics_dt=1 / 120, rendering_dt=1 / 60, physics_prim_path='/World/PhysicsScene')
    physics = UsdPhysics.Scene.Define(world.stage, '/World/PhysicsScene')
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    physics.CreateGravityMagnitudeAttr(9.81)
    cases = {}
    for (index, (name, settings)) in enumerate(variants.items()):
        settings = {**settings, 'current_world_m_s': [0] * 3, 'displaced_volume_m3': 0.005}
        hydro = Hydrodynamics(settings, 10, -10, [[-100, -100], [100, -100], [100, 100], [-100, 100]])
        p = hydro.p
        prim = UsdGeom.Cube.Define(world.stage, '/World/' + name).GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        mass = UsdPhysics.MassAPI.Apply(prim)
        mass.CreateMassAttr(p['mass_kg'])
        mass.CreateCenterOfMassAttr(Gf.Vec3f(*map(float, p['center_of_mass_body_m'])))
        mass.CreateDiagonalInertiaAttr(Gf.Vec3f(*map(float, p['inertia_kg_m2'])))
        mass.CreatePrincipalAxesAttr(Gf.Quatf(1, Gf.Vec3f(0)))
        api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        api.CreateDisableGravityAttr(True)
        api.CreateLinearDampingAttr(0)
        api.CreateAngularDampingAttr(0)
        api.CreateEnableGyroscopicForcesAttr(True)
        fapi = PhysxSchema.PhysxForceAPI.Apply(prim)
        fapi.CreateForceEnabledAttr(True)
        fapi.CreateWorldFrameEnabledAttr(True)
        fapi.CreateModeAttr('force')
        fapi.CreateForceAttr(Gf.Vec3f(0))
        fapi.CreateTorqueAttr(Gf.Vec3f(0))
        robot = world.scene.add(SingleRigidPrim(str(prim.GetPath()), name=name))
        q = np.array([math.cos(0.1), 0, math.sin(0.1), 0]) if name == 'passive_tilt' else np.array([1.0, 0, 0, 0])
        robot.set_default_state(position=np.array([index * 4.0, 0, 0]), orientation=q)
        cases[name] = dict(robot=robot, hydro=hydro, servo=VelocityController(settings), api=fapi, samples=[])
    world.reset()
    for (name, case) in cases.items():
        if name.startswith('level_brake'):
            case['robot'].set_linear_velocity(np.array([0.3, 0, 0]))
        PhysxSchema.PhysxRigidBodyAPI(case['robot'].prim).GetDisableGravityAttr().Set(False)

    def forces(dt):
        t = float(world.current_time)
        for (name, case) in cases.items():
            robot = case['robot']
            (pos, q) = robot.get_world_pose()
            (v, w) = (robot.get_linear_velocity(), robot.get_angular_velocity())
            desired = np.zeros(3)
            if not name.startswith('level_brake') and 2 <= t < 6:
                desired[1 if name == 'sway_stop' else 0] = 0.3
            if name == 'passive_tilt':
                (command, torque) = (np.zeros(3), np.zeros(3))
            else:
                desired[2] = -0.8 * pos[2]
                (command, torque) = case['servo'].step(dt, q, v, w, desired, 0)
            if name.startswith('level_brake'):
                if t < 0.5:
                    command[0] = -6.0
            elif name not in ('passive_tilt', 'sway_stop') and 6 <= t < 6.5:
                command[0] = -6.0
            (f, m, info) = case['hydro'].step(dt, pos, q, v, w, command, torque)
            case['api'].GetForceAttr().Set(Gf.Vec3f(*map(float, f)))
            case['api'].GetTorqueAttr().Set(Gf.Vec3f(*map(float, m)))
            r = rotation_matrix(q)
            case['samples'].append(dict(t=t, position=pos.tolist(), velocity=v.tolist(), orientation=q.tolist(), angular_velocity=w.tolist(), nose_up_deg=float(np.degrees(np.arcsin(np.clip(r[2, 0], -1, 1)))), roll_deg=float(np.degrees(np.arctan2(r[2, 1], r[2, 2]))), hydrodynamics=info))
    world.add_physics_callback('coupled_probe', forces)
    for _ in range(1800):
        world.step(render=True)
    summary = {}
    for (name, case) in cases.items():
        samples = case['samples']
        brake_start = 0 if name.startswith('level_brake') else 6
        brake = [s for s in samples if brake_start <= s['t'] <= brake_start + 3]
        summary[name] = dict(peak_braking_nose_up_deg=max((s['nose_up_deg'] for s in brake)), min_braking_nose_up_deg=min((s['nose_up_deg'] for s in brake)), peak_abs_roll_deg=max((abs(s['roll_deg']) for s in samples)), final_speed_m_s=float(np.linalg.norm(samples[-1]['velocity'])), final_nose_up_deg=samples[-1]['nose_up_deg'], braking_pitch_rise_deg=max((s['nose_up_deg'] for s in brake)) - min(samples, key=lambda s: abs(s['t'] - brake_start))['nose_up_deg'])
    checks = dict(centred_stays_level=max((abs(s['nose_up_deg']) for s in cases['level_brake_centred']['samples'])) < 0.1, braking_creates_nose_up=summary['level_brake']['peak_braking_nose_up_deg'] > 1.0, reverse_line_nose_down=summary['level_brake_reverse']['min_braking_nose_up_deg'] < -1.0, settles_after_braking=abs(summary['level_brake']['final_nose_up_deg']) < 1.0 and summary['level_brake']['final_speed_m_s'] < 0.01, passive_restoring=abs(summary['passive_tilt']['final_nose_up_deg']) < 1.0, lateral_acceleration_rolls=summary['sway_stop']['peak_abs_roll_deg'] > 1.0, finite=all((np.isfinite(s['nose_up_deg']) and np.isfinite(s['velocity']).all() for c in cases.values() for s in c['samples'])))
    report = dict(summary=summary, checks=checks, passed=all(checks.values()), model=coupled, note='Synthetic ablations in real PhysX; not identified vehicle parameters or navigation tests.', cases={name: c['samples'] for (name, c) in cases.items()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report))
    print(json.dumps(dict(summary=summary, checks=checks, passed=report['passed']), indent=2), flush=True)
    assert report['passed'], checks
finally:
    app.close()
