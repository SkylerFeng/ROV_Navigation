"""One isolated real Isaac+EGO+semantic trial; preserve success and failure."""
import argparse,json,os,signal,subprocess,time,hashlib
from pathlib import Path
from run_suite import stop
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--policy',choices=['rule','qwen','deepseek'],default='rule');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--gui',action='store_true');p.add_argument('--domain',type=int,default=137);p.add_argument('--wall-limit',type=float,default=600)
    p.add_argument('--scene-file',type=Path,default=ROOT/'scenes/pool_platform_semantic.usda');a=p.parse_args()
    from semantic_credentials import load_credentials
    # Local rule navigation must not depend on cloud credential configuration.
    if a.policy != 'rule':
        load_credentials(os.environ.get('ROV_SEMANTIC_ENV_FILE'))
    a.scene_file=a.scene_file.resolve();a.output=a.output.resolve()
    if a.output.exists():raise FileExistsError('Choose a new output directory')
    if a.policy!='rule':
        conf=json.loads((ROOT/'config/semantic/providers.json').read_text())[a.policy]
        if not os.environ.get(conf['key_env']):raise RuntimeError('Set '+conf['key_env']+' locally before starting')
    a.output.mkdir(parents=True);env=dict(os.environ,ROS_DOMAIN_ID=str(a.domain),ROV_SCENARIO='platform_semantic',ROV_SEMANTIC='1',ROV_EXPERIMENT_OVERRIDES=str(ROOT/'config/experiments/hydro_components.json'))
    sources=[*ROOT.glob('scripts/*semantic*'),*ROOT.glob('config/semantic/*'),ROOT/'scripts/run_sim.py',ROOT/'scripts/tracker.py',ROOT/'scripts/experiment.py',ROOT/'config/scenarios_semantic.json',ROOT/'config/experiments/hydro_components.json',ROOT/'scenes/pool_platform_semantic.usda',ROOT/'scenes/pool_platform_ego.usda',a.scene_file,ROOT/'logs/semantic_detector_lit/train/weights/best.onnx']
    (a.output/'manifest.json').write_text(json.dumps({'policy':a.policy,'scene':str(a.scene_file),'sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources if f.is_file()},'hydrodynamics':'hydro_components','domain':a.domain},indent=2))
    children=[];streams=[];start=time.monotonic();reason='unknown'
    def launch(name,cmd):
        f=(a.output/(name+'.log')).open('w');streams.append(f)
        process=subprocess.Popen(cmd,env=env,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);return process
    try:
        nav=launch('navigation',['bash','scripts/start_navigation.sh'])
        semantic=launch('semantic',['bash','scripts/start_semantic.sh','--policy',a.policy,'--output',str(a.output/'semantic')])
        sim=launch('simulation',['bash','scripts/start_sim.sh',* ([] if a.gui else ['--headless']),'--scenario','platform_semantic','--scene-file',str(a.scene_file),'--output-dir',str(a.output/'sim'),'--sim-time-limit','310','--wall-time-limit',str(a.wall_limit),'--view','perspective'])
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
    (a.output/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='semantic'}))
if __name__=='__main__':main()
