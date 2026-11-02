"""Run physical probes in Isaac/PhysX without cameras, ROS, or pool assets.

Run with: bash scripts/start_sim.sh ... for navigation; for this probe use
ISAAC_SIM_PATH/python.sh scripts/test_hydrodynamics_isaac.py --output PATH.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
from isaacsim import SimulationApp
app = SimulationApp({'headless': True})
try:
    import math
    import numpy as np
    from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleRigidPrim
    from hydrodynamics import Hydrodynamics, VelocityController, rotation_matrix

    world = World(stage_units_in_meters=1., physics_dt=1/60, rendering_dt=1/60)
    physics = UsdPhysics.Scene.Define(world.stage, '/World/PhysicsScene')
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    physics.CreateGravityMagnitudeAttr(9.81)
    boundary = [[-20, -20], [20, -20], [20, 20], [-20, 20]]
    cases = {}
    for index, name in enumerate(['neutral', 'positive', 'passive_current', 'controlled_current',
                                  'controlled_current_no_integral', 'tilted', 'dry', 'lag']):
        path = '/World/'+name
        prim = UsdGeom.Cube.Define(world.stage, path).GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        mass = UsdPhysics.MassAPI.Apply(prim)
        mass.CreateMassAttr(5.)
        mass.CreateCenterOfMassAttr(Gf.Vec3f(0, 0, .116))
        mass.CreateDiagonalInertiaAttr(Gf.Vec3f(.1635, .1242, .2314))
        mass.CreatePrincipalAxesAttr(Gf.Quatf(1., Gf.Vec3f(0)))
        api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        api.CreateDisableGravityAttr(True)
        api.CreateLinearDampingAttr(0.)
        api.CreateAngularDampingAttr(0.)
        force_api = PhysxSchema.PhysxForceAPI.Apply(prim)
        force_api.CreateForceEnabledAttr(True)
        force_api.CreateWorldFrameEnabledAttr(True)
        force_api.CreateModeAttr('force')
        force_api.CreateForceAttr(Gf.Vec3f(0))
        force_api.CreateTorqueAttr(Gf.Vec3f(0))
        position = np.array([index*2.-6., 0., 0.])
        if name == 'dry':
            position[0] = 30.
        q = np.array([math.cos(.1), math.sin(.1), 0., 0.]) if name == 'tilted' else np.array([1., 0., 0., 0.])
        robot = world.scene.add(SingleRigidPrim(path, name=name))
        robot.set_default_state(position=position, orientation=q)
        settings = {'current_world_m_s': [.08, .04, 0] if 'current' in name else [0, 0, 0],
                    'displaced_volume_m3': .00505 if name in ['positive', 'controlled_current', 'controlled_current_no_integral'] else .005}
        if name == 'controlled_current_no_integral':
            settings['velocity_ki'] = [0., 0., 0.]
        hydro = Hydrodynamics(settings, 10., -10., boundary)
        cases[name] = dict(robot=robot, hydro=hydro, servo=VelocityController(settings), api=force_api,
                           start=position, samples=[], elapsed=0.)
    world.reset()
    for case in cases.values():
        PhysxSchema.PhysxRigidBodyAPI(case['robot'].prim).GetDisableGravityAttr().Set(False)

    def forces(dt):
        for name, case in cases.items():
            robot, hydro = case['robot'], case['hydro']
            pos, q = robot.get_world_pose()
            v, angular = robot.get_linear_velocity(), robot.get_angular_velocity()
            command, torque = np.zeros(3), np.zeros(3)
            if name.startswith('controlled_current'):
                desired = .8*(case['start']-pos)
                command, torque = case['servo'].step(dt, q, v, angular, desired, 0.)
            if name == 'lag':
                command[0] = 6.
            force, moment, info = hydro.step(dt, pos, q, v, angular, command, torque)
            case['api'].GetForceAttr().Set(Gf.Vec3f(*map(float, force)))
            case['api'].GetTorqueAttr().Set(Gf.Vec3f(*map(float, moment)))
            case['elapsed'] += dt
            tilt = math.acos(float(np.clip(rotation_matrix(q)[2, 2], -1, 1)))
            case['samples'].append(dict(t=case['elapsed'], position=pos.tolist(), velocity=v.tolist(),
                                        tilt_rad=tilt, actuator_x_n=info['actuator_force_body_n'][0]))
    for _ in range(1800):
        forces(1/60)
        world.step(render=True)
    results = {name: case['samples'][-1] for name, case in cases.items()}
    lag = min(cases['lag']['samples'], key=lambda s: abs(s['t']-.25))
    dry = min(cases['dry']['samples'], key=lambda s: abs(s['t']-.2))
    checks = {
        'neutral_holds_height': abs(results['neutral']['position'][2]) < .01,
        'positive_buoyancy_rises': results['positive']['position'][2] > .2,
        'passive_drift_matches_flow': np.linalg.norm(np.array(results['passive_current']['velocity'])-[.08, .04, 0]) < .001,
        'controller_holds_against_current': np.linalg.norm(np.array(results['controlled_current']['position'])-cases['controlled_current']['start']) < .005,
        'integral_reduces_stationkeeping_bias': np.linalg.norm(np.array(results['controlled_current_no_integral']['position'])-cases['controlled_current_no_integral']['start']) > .01,
        'buoyancy_restores_tilt': results['tilted']['tilt_rad'] < .01,
        'dry_body_falls_under_gravity': abs(dry['velocity'][2]+9.81*(dry['t']-1/60)) < .1,
        'actuator_tau_matches_sim_clock': abs(lag['actuator_x_n']-6*(1-math.exp(-1))) < 1e-5,
        'physics_steps_match_elapsed': abs(cases['neutral']['elapsed']-world.current_time) < .1,
    }
    report = dict(checks={k: bool(v) for k, v in checks.items()}, passed=all(checks.values()),
                  duration_s=float(world.current_time), final=results,
                  lag_at_one_tau=lag, dry_at_point_two_s=dry,
                  note='Synthetic mass/volume/drag; physical probes, not robot parameter identification.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    assert report['passed'], report['checks']
finally:
    app.close()
