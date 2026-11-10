"""Serial real-API Isaac trials; always preserve failed runs. No parallel GPU use."""
import argparse,json,subprocess,sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=Path,default=root/'config/semantic/diversity_suite.json')
    p.add_argument('--env-file',type=Path,default=root/'.env.semantic');p.add_argument('--gui',action='store_true')
    p.add_argument('--domain',type=int,default=143);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);rows=[]
    for case in json.loads(a.cases.read_text()):
        directory=a.output/case['name']
        cmd=[sys.executable,str(root/'scripts/run_semantic_trial.py'),'--policy','qwen',
             '--env-file',str(a.env_file.resolve()),'--instruction',case['instruction'],
             '--scene-file',case['scene'],'--domain',str(a.domain),'--output',str(directory.resolve())]
        if a.gui:cmd.append('--gui')
        for option in ('task_config','runtime_config','navigation_config'):
            if case.get(option):cmd.extend(['--'+option.replace('_','-'),case[option]])
        if case.get('wall_limit'):cmd.extend(['--wall-limit',str(case['wall_limit'])])
        completed=subprocess.run(cmd,cwd=root)
        row={**case,'returncode':completed.returncode,'run':str(directory)}
        summary=directory/'summary.json'
        if summary.exists():row['stop_reason']=json.loads(summary.read_text())['stop_reason']
        rows.append(row);(a.output/'suite.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        print(json.dumps(row,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
