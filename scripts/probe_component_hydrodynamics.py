"""Real PhysX probes for mesh-derived component drag; uncalibrated coefficients."""
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
    coupled = json.loads((root / 'config/experiments/hydro_components.json').read_text())['hydrodynamics']
    variants = {name: coupled for name in ('braking', 'coast', 'yaw_stop', 'moving_turn')}
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
        if name in ('braking', 'coast'):
            case['robot'].set_linear_velocity(np.array([0.3, 0, 0]))
        PhysxSchema.PhysxRigidBodyAPI(case['robot'].prim).GetDisableGravityAttr().Set(False)

    def forces(dt):
        t = float(world.current_time)
        for (name, case) in cases.items():
            robot = case['robot']
            (pos, q) = robot.get_world_pose()
            (v, w) = (robot.get_linear_velocity(), robot.get_angular_velocity())
            desired = np.zeros(3)
            yaw_rate = 0.
            if name == 'moving_turn':
                r = rotation_matrix(q)
                desired = r @ np.array([.2, 0, 0]) if t < 10 else desired
                yaw_rate = .2 if 2 <= t < 8 else 0.
            elif name == 'yaw_stop':
                yaw_rate = .2 if 2 <= t < 6 else 0.
            desired[2] = -.8 * pos[2]
            command, torque = case['servo'].step(dt, q, v, w, desired, yaw_rate)
            if name == 'coast':
                command[:] = 0
                torque[:] = 0
            if name == 'braking' and t < .5:
                command[0] = -6.
            (f, m, info) = case['hydro'].step(dt, pos, q, v, w, command, torque)
            case['api'].GetForceAttr().Set(Gf.Vec3f(*map(float, f)))
            case['api'].GetTorqueAttr().Set(Gf.Vec3f(*map(float, m)))
            r = rotation_matrix(q)
            case['samples'].append(dict(t=t, position=pos.tolist(), velocity=v.tolist(), orientation=q.tolist(), angular_velocity=w.tolist(), nose_up_deg=float(np.degrees(np.arcsin(np.clip(r[2, 0], -1, 1)))), roll_deg=float(np.degrees(np.arctan2(r[2, 1], r[2, 2]))), hydrodynamics=info))
    world.add_physics_callback('coupled_probe', forces)
    for _ in range(1200):
        world.step(render=True)
    summary = {}
    for name, case in cases.items():
        rows = case['samples']
        first = rows[0]
        final = rows[-1]
        positions = np.array([r['position'] for r in rows])
        speed = np.array([np.linalg.norm(r['velocity']) for r in rows])
        yaw = np.unwrap([math.atan2(rotation_matrix(r['orientation'])[1,0], rotation_matrix(r['orientation'])[0,0]) for r in rows])
        stop_time = 8 if name == 'moving_turn' else 6
        stop_index = min(range(len(rows)), key=lambda i: abs(rows[i]['t']-stop_time))
        summary[name] = dict(max_abs_pitch_deg=max(abs(r['nose_up_deg']) for r in rows),
            max_abs_roll_deg=max(abs(r['roll_deg']) for r in rows),
            final_speed_m_s=float(np.linalg.norm(final['velocity'])),
            yaw_rate_at_command_stop_rad_s=rows[stop_index]['angular_velocity'][2],
            yaw_command_stop_time_s=stop_time,
            yaw_continuation_after_stop_deg=float(np.degrees(yaw[-1]-yaw[stop_index])),
            final_yaw_rate_rad_s=final['angular_velocity'][2],
            max_forward_excursion_m=float((positions[:, 0]-positions[0, 0]).max()),
            speed_at_02s_m_s=float(speed[min(range(len(rows)), key=lambda i: abs(rows[i]['t']-.2))]),
            displacement_m=float(np.linalg.norm(np.array(final['position'])-first['position'])),
            max_relative_drag_power_w=max(r['hydrodynamics']['component_hydrodynamics']['relative_drag_power_w'] for r in rows))
    checks = dict(finite=all(np.isfinite(r['velocity']).all() and np.isfinite(r['angular_velocity']).all() for c in cases.values() for r in c['samples']),
        passive_drag=all(v['max_relative_drag_power_w'] <= 1e-9 for v in summary.values()),
        active_brake_settles=summary['braking']['final_speed_m_s'] < .02,
        yaw_stop_settles=abs(summary['yaw_stop']['final_yaw_rate_rad_s']) < .01,
        yaw_stop_continues=abs(summary['yaw_stop']['yaw_continuation_after_stop_deg']) > .01)
    report = dict(summary=summary, checks=checks, passed=all(checks.values()), model=coupled,
        note='Actual PhysX, mesh-derived drag with uncalibrated coefficients; buoyancy, added mass and thrust line remain parameter hypotheses. Coast has no active depth hold.',
        cases={name: c['samples'][::12] for name,c in cases.items()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report))
    print(json.dumps(dict(summary=summary,checks=checks,passed=report['passed']),indent=2),flush=True)
    assert report['passed'], checks
finally:
    app.close()
