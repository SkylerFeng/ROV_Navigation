"""One isolated real Isaac+EGO+semantic trial; preserve success and failure."""
import argparse,json,os,signal,subprocess,time,hashlib
from pathlib import Path
from run_suite import stop
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--policy',choices=['rule','qwen','deepseek'],default='rule');p.add_argument('--output',type=Path)
    p.add_argument('--gui',action='store_true');p.add_argument('--domain',type=int,default=137);p.add_argument('--wall-limit',type=float,default=600)
    p.add_argument('--scene-file',type=Path,default=ROOT/'scenes/pool_platform_semantic.usda')
    p.add_argument('--instruction',help='Resolve a natural-language command with the selected cloud model before launch')
    p.add_argument('--navigation-config',type=Path,help='Navigation tuning JSON patch')
    p.add_argument('--task-config',type=Path,help='JSON patch over config/semantic/task.json')
    p.add_argument('--runtime-config',type=Path,help='JSON patch over config/semantic/runtime.json')
    p.add_argument('--providers-config',type=Path,help='JSON patch over config/semantic/providers.json')
    p.add_argument('--overrides',type=Path,default=ROOT/'config/experiments/hydro_components.json')
    p.add_argument('--model',type=Path,default=ROOT/'logs/semantic_detector_lit/train/weights/best.onnx')
    p.add_argument('--env-file',type=Path,help='Local credentials; never copied into results')
    p.add_argument('--view',choices=['top','perspective'],default='perspective')
    p.add_argument('--check-config',action='store_true',help='Validate and print effective config without starting Isaac or calling API')
    a=p.parse_args()
    if not a.check_config and a.output is None:p.error('--output is required unless --check-config is used')
    if a.instruction and a.policy=='rule':p.error('--instruction requires qwen or deepseek; rule uses task-config')
    if a.wall_limit<=0:p.error('--wall-limit must be positive')
    from semantic_config import load_task,load_runtime,load_providers,effective_provider
    task=load_task(a.task_config);runtime=load_runtime(a.runtime_config);providers=load_providers(a.providers_config)
    if runtime['verification']['distance_near_margin_m']>=task['surface_standoff_m']:
        p.error('verification.distance_near_margin_m must be smaller than task.surface_standoff_m')
    from semantic_credentials import load_credentials
    # Local rule navigation must not depend on cloud credential configuration.
    if a.policy != 'rule':
        load_credentials(a.env_file or os.environ.get('ROV_SEMANTIC_ENV_FILE'))
        providers[a.policy]=effective_provider(a.policy,providers)
    a.scene_file=a.scene_file.resolve();a.overrides=a.overrides.resolve();a.model=a.model.resolve()
    for name,path in [('scene',a.scene_file),('overrides',a.overrides),('model',a.model)]:
        if not path.is_file():p.error(f'{name} file not found: {path}')
    from experiment import load_experiment
    previous_nav=os.environ.get('ROV_NAVIGATION_CONFIG')
    if a.navigation_config:os.environ['ROV_NAVIGATION_CONFIG']=str(a.navigation_config.resolve())
    previous=os.environ.get('ROV_EXPERIMENT_OVERRIDES')
    try:
        os.environ['ROV_EXPERIMENT_OVERRIDES']=str(a.overrides)
        experiment=load_experiment('platform_semantic')
    finally:
        if previous_nav is None:os.environ.pop('ROV_NAVIGATION_CONFIG',None)
        else:os.environ['ROV_NAVIGATION_CONFIG']=previous_nav
        if previous is None:os.environ.pop('ROV_EXPERIMENT_OVERRIDES',None)
        else:os.environ['ROV_EXPERIMENT_OVERRIDES']=previous
    experiment['scene_file']=str(a.scene_file)
    effective={'policy':a.policy,'scene':str(a.scene_file),'model':str(a.model),'task':task,'runtime':runtime,
               'providers':providers,'experiment':experiment,'domain':a.domain,'view':a.view,
               'wall_limit_s':a.wall_limit,'sim_limit_s':task['timeout_sim_s']+10,
               'credential_present':bool(os.getenv(providers[a.policy]['key_env'])) if a.policy!='rule' else None}
    if a.check_config:
        if a.instruction:effective['instruction_pending_resolution']=a.instruction
        print(json.dumps(effective,ensure_ascii=False,indent=2));return
    a.output=a.output.resolve()
    if a.output.exists():raise FileExistsError('Choose a new output directory')
    if a.policy!='rule':
        conf=providers[a.policy]
        if not os.environ.get(conf['key_env']):raise RuntimeError('Set '+conf['key_env']+' locally before starting')
    a.output.mkdir(parents=True)
    if a.instruction:
        from semantic_instruction import resolve_instruction,apply_resolution
        try:
            parsed=resolve_instruction(a.instruction,a.policy,providers[a.policy],runtime['llm'])
            (a.output/'instruction.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=2))
        except Exception as exc:
            (a.output/'instruction_error.json').write_text(json.dumps({'type':type(exc).__name__}))
            raise RuntimeError('Instruction API failed; no simulation started. See instruction_error.json') from None
        if parsed['resolution']['status']!='accepted':
            summary={'stop_reason':'instruction_'+parsed['resolution']['status'],'reason':parsed['resolution']['reason']}
            (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False));return
        task=apply_resolution(task,parsed);effective['task']=task;effective['sim_limit_s']=task['timeout_sim_s']+10
    snapshots=a.output/'config';snapshots.mkdir()
    for name,value in [('task',task),('runtime',runtime),('providers',providers),('experiment',experiment)]:
        (snapshots/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    (a.output/'effective_config.json').write_text(json.dumps(effective,ensure_ascii=False,indent=2)+'\n')
    env=dict(os.environ,ROS_DOMAIN_ID=str(a.domain),ROV_SCENARIO='platform_semantic',ROV_SEMANTIC='1',
             ROV_EXPERIMENT_OVERRIDES=str(snapshots/'experiment.json'),ROV_SEMANTIC_RUNTIME_CONFIG=str(snapshots/'runtime.json'))
    env.pop('ROV_NAVIGATION_CONFIG',None)  # frozen experiment is authoritative for children
    # load_experiment accepts config keys, not its own provenance fields.
    experiment_override={k:v for k,v in experiment.items() if k not in ('scenario','scene_file','overrides_file')}
    (snapshots/'experiment.json').write_text(json.dumps(experiment_override,ensure_ascii=False,indent=2)+'\n')
    sources=[*ROOT.glob('scripts/*semantic*'),*ROOT.glob('config/semantic/*'),ROOT/'scripts/run_sim.py',ROOT/'scripts/tracker.py',ROOT/'scripts/experiment.py',ROOT/'config/scenarios_semantic.json',ROOT/'config/experiments/hydro_components.json',ROOT/'scenes/pool_platform_semantic.usda',ROOT/'scenes/pool_platform_ego.usda',a.scene_file,ROOT/'logs/semantic_detector_lit/train/weights/best.onnx']
    sources += [ROOT/'scripts/navigation_config.py',ROOT/'scripts/navigation.launch.py',ROOT/'scripts/tracking_control.py',ROOT/'scripts/local_map.py',*ROOT.glob('config/navigation/*.json')]
    sources += [*ROOT.glob('ros_ws/src/plan_manage/src/*.cpp'),*ROOT.glob('ros_ws/src/plan_manage/include/**/*.h'),
                ROOT/'ros_ws/install/ego_planner/lib/ego_planner/ego_planner_node',
                *ROOT.glob('ros_ws/install/ego_planner/lib/*.so')]
    sources += [a.model,a.overrides,*snapshots.glob('*.json')]
    (a.output/'manifest.json').write_text(json.dumps({'policy':a.policy,'scene':str(a.scene_file),'sha256':{str(f.relative_to(ROOT) if f.is_relative_to(ROOT) else f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources if f.is_file()},'hydrodynamics':experiment.get('hydrodynamics',{}).get('component_model_file'),'domain':a.domain},indent=2))
    children=[];streams=[];start=time.monotonic();reason='unknown'
    def launch(name,cmd):
        f=(a.output/(name+'.log')).open('w');streams.append(f)
        process=subprocess.Popen(cmd,env=env,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);return process
    try:
        nav=launch('navigation',['bash','scripts/start_navigation.sh'])
        semantic=launch('semantic',['bash','scripts/start_semantic.sh','--policy',a.policy,'--output',str(a.output/'semantic'),
                                   '--model',str(a.model),'--task-config',str(snapshots/'task.json'),
                                   '--runtime-config',str(snapshots/'runtime.json'),'--providers-config',str(snapshots/'providers.json')])
        sim=launch('simulation',['bash','scripts/start_sim.sh',* ([] if a.gui else ['--headless']),'--scenario','platform_semantic','--scene-file',str(a.scene_file),'--output-dir',str(a.output/'sim'),'--sim-time-limit',str(task['timeout_sim_s']+10),'--wall-time-limit',str(a.wall_limit),'--view',a.view])
        while time.monotonic()-start<a.wall_limit+100:
            result=a.output/'semantic/result.json'
            if result.exists():
                reason=json.loads(result.read_text())['status']
                try:sim.wait(timeout=20)
                except subprocess.TimeoutExpired:pass
                break
            if sim.poll() is not None or semantic.poll() is not None or nav.poll() is not None:reason='process_exited';break
            time.sleep(.5)
        else:reason='wall_timeout'
    finally:
        for process in reversed(children):stop(process)
        for f in streams:f.close()
    result={'stop_reason':reason,'wall_seconds':time.monotonic()-start}
    if (a.output/'semantic/result.json').exists():result['semantic']=json.loads((a.output/'semantic/result.json').read_text())
    if 'semantic' in result:result['semantic_reason']=result['semantic'].get('reason')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='semantic'}))
if __name__=='__main__':main()
