"""Sequential rule/LLM trials with identical scenes; missing keys are explicit skips."""
import argparse,json,os,subprocess
from pathlib import Path
from semantic_credentials import load_credentials
from semantic_config import load_providers
from analyze_semantic_trial import analyze
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--policies',nargs='+',choices=['rule','deepseek','qwen'],default=['rule','deepseek'])
    p.add_argument('--scenes',nargs='+',choices=['basic','screened','relocated','occluded'],default=['basic','screened'])
    p.add_argument('--repeats',type=int,default=1);p.add_argument('--env-file',type=Path)
    for option in ('task-config','runtime-config','providers-config','overrides','model'):
        p.add_argument('--'+option,type=Path)
    a=p.parse_args()
    if a.repeats<1:raise ValueError('repeats must be positive')
    if any(policy != 'rule' for policy in a.policies):
        load_credentials(a.env_file or os.environ.get('ROV_SEMANTIC_ENV_FILE'))
    if a.output.exists():raise FileExistsError('Choose a fresh comparison output directory')
    a.output.mkdir(parents=True);results=[]
    providers=load_providers(a.providers_config)
    extra=[]
    for option in ('task-config','runtime-config','providers-config','overrides','model','env-file'):
        value=getattr(a,option.replace('-','_'))
        if value:extra.extend(['--'+option,str(value.resolve())])
    for scene in a.scenes:
        filename='pool_platform_semantic'+('' if scene=='basic' else '_'+scene)+'.usda'
        for repeat in range(a.repeats):
            for policy in a.policies:
                row={'scene':scene,'repeat':repeat,'policy':policy}
                if policy!='rule' and not os.getenv(providers[policy]['key_env']):
                    row.update(status='NOT_RUN',reason='missing_local_api_key')
                else:
                    directory=a.output/f'{scene}_{policy}_{repeat:02d}'
                    child=subprocess.run(['python3',str(ROOT/'scripts/run_semantic_trial.py'),'--policy',policy,'--scene-file',str(ROOT/'scenes'/filename),'--output',str(directory.resolve()),*extra],cwd=ROOT)
                    if (directory/'semantic/result.json').exists() and (directory/'sim/run.json').exists():
                        row.update(analyze(directory,directory/'analysis'))
                        row['status']=row['runtime_status']
                    else:row.update(status='ERROR',returncode=child.returncode)
                results.append(row)
                (a.output/'comparison.json').write_text(json.dumps({'runs':results,'note':'NOT_RUN is not failure or zero latency. Trials are serial; no success-rate claim from one repeat.'},ensure_ascii=False,indent=2))
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
