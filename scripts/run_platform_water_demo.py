"""Known-map obstacle avoidance and hydrodynamics demo in Platform_black_water.
Run using Isaac Sim python.sh. Source assets are referenced, never overwritten.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--headless', action='store_true')
parser.add_argument('--duration', type=float, default=75.)
parser.add_argument('--waypoint-only', action='store_true', help='Run the earlier obstacle-free waypoint demo')
parser.add_argument('--output-dir', type=Path, default=Path('logs/platform_navigation_demo'))
args = parser.parse_args()
args.output_dir = args.output_dir.resolve()
args.output_dir.mkdir(parents=True, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless, 'width': 1280, 'height': 720})
try:
    import numpy as np
    import carb
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade, UsdLux, PhysxSchema, PhysicsSchemaTools
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleRigidPrim
    from isaacsim.core.utils.viewports import set_camera_view
    from omni.kit.viewport.utility import get_active_viewport, capture_viewport_to_file
    from omni.physx import get_physx_simulation_interface
    from omni.physx.bindings._physx import ContactEventType
    from hydrodynamics import Hydrodynamics, VelocityController, parameters

    source = '/home/ache/OceanSim-Highbay/data/Platform(new1)/Platform_black_water.usda'
    world = World(stage_units_in_meters=1., physics_dt=1/60, rendering_dt=1/60)
    stage = world.stage
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    pool = UsdGeom.Xform.Define(stage, '/World/Pool').GetPrim()
    pool.GetReferences().AddReference(source)
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(pool)
    local_boundary = pool.GetAttribute('oceansim:water:boundaryXY').Get()
    boundary = [list(transform.Transform(Gf.Vec3d(float(x),float(y),0)))[:2] for x,y in local_boundary]
    surface = transform.Transform(Gf.Vec3d(0,0,pool.GetAttribute('oceansim:water:surfaceZ').Get()))[2]
    bottom = transform.Transform(Gf.Vec3d(0,0,pool.GetAttribute('oceansim:water:bottomZ').Get()))[2]
    # Display override only: keep original surface geometry and source transforms.
    for prim in stage.Traverse():
        if str(prim.GetPath()).startswith('/World/Pool/Water') and prim.IsA(UsdShade.Shader):
            shader = UsdShade.Shader(prim)
            shader.CreateInput('opacity', Sdf.ValueTypeNames.Float).Set(.10)
            shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(.65)
    for setting in ['/rtx/raytracing/fractionalCutoutOpacity', '/rtx/pathtracing/fractionalCutoutOpacity']:
        carb.settings.get_settings().set(setting, True)
    light = UsdLux.DomeLight.Define(stage, '/World/DemoLight')
    light.CreateIntensityAttr(650.)
    physics = UsdPhysics.Scene.Define(stage, '/World/PhysicsScene')
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1))
    physics.CreateGravityMagnitudeAttr(9.81)
    waypoints = np.array([[3.,1.5,-.30],[5.,1.5,-.30],[7.,1.5,-.30],[7.,2.5,-.30]])
    navigation = None
    obstacles = []
    if not args.waypoint_only:
        from platform_navigation import plan
        obstacles = [[5.,1.5,.35]]
        for i,(x,y,r) in enumerate(obstacles):
            obstacle = UsdGeom.Cylinder.Define(stage, f'/World/Obstacle_{i}')
            obstacle.CreateRadiusAttr(r)
            obstacle.CreateHeightAttr(.8)
            obstacle.CreateAxisAttr('Z')
            obstacle.AddTranslateOp().Set(Gf.Vec3d(x,y,-.25))
            obstacle.CreateDisplayColorAttr([Gf.Vec3f(.95,.25,.05)])
            UsdPhysics.CollisionAPI.Apply(obstacle.GetPrim())
        waypoints,navigation = plan(stage,boundary,[3.05,1.5,-.30],[7.1,1.5,-.30],obstacles)
        print('PLANNED',json.dumps(navigation),flush=True)
        planned = UsdGeom.BasisCurves.Define(stage,'/World/PlannedRoute')
        planned.CreateTypeAttr('linear')
        planned.CreatePointsAttr([Gf.Vec3f(float(x),float(y),surface+.015) for x,y,z in waypoints])
        planned.CreateCurveVertexCountsAttr([len(waypoints)])
        planned.CreateWidthsAttr([.018])
        planned.CreateDisplayColorAttr([Gf.Vec3f(.1,.9,1.)])
    settings = {'current_world_m_s':[0.,.06,0.]}
    p = parameters(settings)
    body = UsdGeom.Xform.Define(stage, '/World/ROV').GetPrim()
    body.GetReferences().AddReference('/home/ache/OceanSim_assets/Bluerov/BROV_low.usd')
    UsdPhysics.RigidBodyAPI.Apply(body)
    mass = UsdPhysics.MassAPI.Apply(body)
    mass.CreateMassAttr(p['mass_kg'])
    mass.CreateCenterOfMassAttr(Gf.Vec3f(*p['center_of_mass_body_m']))
    mass.CreateDiagonalInertiaAttr(Gf.Vec3f(*p['inertia_kg_m2']))
    mass.CreatePrincipalAxesAttr(Gf.Quatf(1.,Gf.Vec3f(0)))
    # One collision hull; visual submeshes must not create additional colliders.
    for prim in stage.Traverse():
        if str(prim.GetPath()).startswith('/World/ROV/') and prim.HasAPI(UsdPhysics.CollisionAPI):
            UsdPhysics.CollisionAPI(prim).CreateCollisionEnabledAttr(False)
    hull = UsdGeom.Cube.Define(stage, '/World/ROV/Hull')
    hull.CreateSizeAttr(1.)
    hull.AddTranslateOp().Set(Gf.Vec3d(*p['center_of_mass_body_m']))
    hull.AddScaleOp().Set(Gf.Vec3f(*p['hull_size_m']))
    hull.MakeInvisible()
    UsdPhysics.CollisionAPI.Apply(hull.GetPrim())
    rigid = PhysxSchema.PhysxRigidBodyAPI.Apply(body)
    rigid.CreateDisableGravityAttr(True)
    rigid.CreateLinearDampingAttr(0.)
    rigid.CreateAngularDampingAttr(0.)
    force_api = PhysxSchema.PhysxForceAPI.Apply(body)
    force_api.CreateForceEnabledAttr(True)
    force_api.CreateWorldFrameEnabledAttr(True)
    force_api.CreateModeAttr('force')
    force_api.CreateForceAttr(Gf.Vec3f(0))
    force_api.CreateTorqueAttr(Gf.Vec3f(0))
    PhysxSchema.PhysxContactReportAPI.Apply(body).CreateThresholdAttr(0.)
    contacts = []
    def on_contacts(headers, data):
        for h in headers:
            if h.type == ContactEventType.CONTACT_LOST:
                continue
            pair = [str(PhysicsSchemaTools.intToSdfPath(v)) for v in [h.collider0,h.collider1]]
            if any(path.startswith('/World/ROV') for path in pair):
                contacts.append({'t':float(world.current_time),'pair':pair,'type':int(h.type)})
    subscription = get_physx_simulation_interface().subscribe_contact_report_events(on_contacts)
    robot = world.scene.add(SingleRigidPrim('/World/ROV', name='rov'))
    robot.set_default_state(position=waypoints[0], orientation=np.array([1.,0,0,0]))
    hydro = Hydrodynamics(settings,surface,bottom,boundary)
    servo = VelocityController(settings)
    # Above-water trace is an annotation, not a second simulated robot.
    trace = UsdGeom.BasisCurves.Define(stage, '/World/ActualTrajectory')
    trace.CreateTypeAttr('linear')
    trace.CreateWidthsAttr([.025])
    trace.CreateDisplayColorAttr([Gf.Vec3f(1.,.35,.03)])
    for i, pos in enumerate([waypoints[0],waypoints[-1]]):
        marker = UsdGeom.Sphere.Define(stage, f'/World/Waypoint_{i}')
        marker.CreateRadiusAttr(.065)
        marker.AddTranslateOp().Set(Gf.Vec3d(float(pos[0]),float(pos[1]),surface+.03))
        marker.CreateDisplayColorAttr([Gf.Vec3f(.2,1.,.25)])
    world.reset()
    set_camera_view(eye=np.array([5.,-.5,2.4]), target=np.array([5.,1.6,-.2]))
    for _ in range(20):
        app.update()
    world.reset()
    robot.set_world_pose(position=waypoints[0], orientation=np.array([1.,0,0,0]))
    robot.set_linear_velocity(np.zeros(3))
    robot.set_angular_velocity(np.zeros(3))
    contacts.clear()
    stage.GetRootLayer().Export(str(args.output_dir/'demo_scene.usda'))
    rigid.GetDisableGravityAttr().Set(False)
    samples, trace_points, captures = [], [], []
    state = {'target':1,'done':False}
    def update_forces(dt):
        pos,q = robot.get_world_pose()
        v,w = robot.get_linear_velocity(),robot.get_angular_velocity()
        target = waypoints[state['target']]
        error = target-pos
        if np.linalg.norm(error)<(.06 if navigation else .08):
            if state['target']<len(waypoints)-1:
                state['target']+=1
            else:
                state['done']=True
        desired = .8*(waypoints[state['target']]-pos)
        desired *= min(1.,.23/max(np.linalg.norm(desired),1e-10))
        command,torque = servo.step(dt,q,v,w,desired,0.)
        force,moment,details = hydro.step(dt,pos,q,v,w,command,torque)
        force_api.GetForceAttr().Set(Gf.Vec3f(*map(float,force)))
        force_api.GetTorqueAttr().Set(Gf.Vec3f(*map(float,moment)))
        samples.append({'t':float(world.current_time),'position':pos.tolist(),'velocity':v.tolist(),
                        'target':state['target'],**details})
    world.add_physics_callback('water_forces',update_forces)
    for step in range(int(args.duration*60)):
        if not app.is_running(): break
        world.step(render=True)
        if step%30==0:
            pos,_ = robot.get_world_pose()
            set_camera_view(eye=np.array([float(pos[0]),float(pos[1])-2.,2.4]), target=np.array([float(pos[0]),float(pos[1]),-.2]))
            trace_points.append(Gf.Vec3f(float(pos[0]),float(pos[1]),surface+.04))
            if len(trace_points)>1:
                trace.GetPointsAttr().Set(trace_points)
                trace.GetCurveVertexCountsAttr().Set([len(trace_points)])
            dest = args.output_dir/f'frame_{step//30:04d}.png'
            captures.append(capture_viewport_to_file(get_active_viewport(),str(dest)))
        if step%600==0: print(f'DEMO t={step/60:.1f} target={state["target"]}',flush=True)
    world.remove_physics_callback('water_forces')
    world.pause()
    for _ in range(15): app.update()
    positions = np.array([s['position'] for s in samples])
    final_pos,_ = robot.get_world_pose()
    report = {'source_asset':source,'control':'A* known-map navigation / velocity PI; not sensor-based EGO' if navigation else 'waypoint position / velocity PI',
              'navigation':navigation,
              'hydrodynamics':{k:v.tolist() if hasattr(v,'tolist') else v for k,v in p.items()},
              'water_boundary_world':boundary,'surface_z':float(surface),'bottom_z':float(bottom),
              'source_transform':np.array(transform).tolist(),'waypoints':waypoints.tolist(),
              'duration_s':float(world.current_time),'completed':state['done'],
              'final_error_m':float(np.linalg.norm(final_pos-waypoints[-1])),
              'path_length_m':float(np.linalg.norm(np.diff(positions,axis=0),axis=1).sum()),
              'max_depth_error_m':float(np.abs(positions[:,2]+.30).max()),
              'min_submerged_fraction':min(s['submerged_fraction'] for s in samples),
              'contacts':contacts,'samples':samples}
    if obstacles:
        report['min_obstacle_hull_clearance_m'] = float(min(np.linalg.norm(positions[:,:2]-[x,y],axis=1).min()-r-np.linalg.norm(p['hull_size_m'][:2])/2 for x,y,r in obstacles))
    (args.output_dir/'motion.json').write_text(json.dumps(report,indent=2)+'\n')
    print('DEMO_RESULT', json.dumps({k:v for k,v in report.items() if k not in ['samples','hydrodynamics']}),flush=True)
finally:
    app.close()
