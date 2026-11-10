"""Real text API evaluation; synthetic decision observations, NOT navigation trials."""
import argparse,json
from pathlib import Path
from semantic_credentials import load_credentials
from semantic_instruction import resolve_instruction
from semantic_llm import JSONPolicy

def main():
    p=argparse.ArgumentParser();p.add_argument('--provider',default='qwen',choices=['qwen','deepseek'])
    p.add_argument('--env-file',default='.env.semantic');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();load_credentials(a.env_file)
    if a.output.exists():raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    cases=json.loads((Path(__file__).resolve().parents[1]/'config/semantic/command_eval.json').read_text())
    rows=[]
    for i,case in enumerate(cases):
        row={'case':case,'passed':False,'decision_passed':None}
        try:
            record=resolve_instruction(case['instruction'],a.provider);row['parse']=record
            r=record['resolution'];row['passed']=[r['status'],r['category'],r['color']]==case['expected']
            if 'expected_distance' in case:row['passed'] &= r['surface_standoff_m']==case['expected_distance']
            if row['passed'] and r['status']=='accepted':
                objects=[{'id':color+'_'+category,'confirmed':True,'color':color,'category':category,'observation_age_s':0.1}
                         for color in ('yellow','blue','red') for category in ('pipe','box')]
                candidates=[{'id':'approach_'+o['id'],'kind':'approach','object_id':o['id'],'reachable':True,'path_length_m':1.} for o in objects]
                observation={'task_id':'command_eval','observation_id':i,'instruction':case['instruction'],
                             'target':{'color':r['color'],'category':r['category']},'scan_completed':True,
                             'objects':objects,'candidates':candidates,'last_action_result':'evaluation'}
                action,meta=JSONPolicy(a.provider).decide(observation)
                row.update(decision=action,decision_metadata=meta,
                           decision_passed=action.get('action')=='approach' and action.get('object_id')==r['color']+'_'+r['category'])
        except Exception as exc:row['error_type']=type(exc).__name__
        rows.append(row);a.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        print(json.dumps({'case':i,'passed':row['passed'],'decision_passed':row['decision_passed']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
