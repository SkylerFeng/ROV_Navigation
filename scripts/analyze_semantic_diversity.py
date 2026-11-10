"""Audit a finished serial suite, including failures; no simulator or API calls."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import shutil
from pathlib import Path

from analyze_semantic_trial import analyze


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',type=Path,help='Completed runner suite.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[];sources=[]
    for case in json.loads(args.suite.read_text()):
        run=Path(case['run']);folder=args.output/case['name']
        row={'name':case['name'],'instruction':case['instruction'],'run':str(run)}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                audit=analyze(run,folder)
            row.update(status=audit['runtime_status'],reason=audit['reason'],
                       offline_verified=audit['offline_verified'],exploration_verified=audit['exploration_verified'],
                       simulation_seconds=audit['simulation_seconds'],path_length_m=audit['path_length_m'],
                       contact_pairs=audit['contact_pairs'],surface_distance_m=audit.get('final_target_surface_distance_xy_m'),
                       contact_evidence=audit['contact_evidence'],
                       decision_api_calls=audit['llm_calls'],instruction_api_calls=int((run/'instruction.json').exists()))
        except (ValueError,FileNotFoundError) as exc:
            row.update(status='INCOMPLETE',reason=str(exc),offline_verified=False)
        rows.append(row)
        folder.mkdir(parents=True,exist_ok=True)
        for filename in ('manifest.json','instruction.json','config/task.json','config/runtime.json','config/navigation.json'):
            original=run/filename
            if original.is_file():
                destination=folder/filename;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(original,destination)
        source={'run':str(run),'files':{}}
        for filename in ('manifest.json','instruction.json','config/task.json','summary.json','semantic/result.json','sim/run.json'):
            path=run/filename
            if path.is_file():source['files'][filename]=hashlib.sha256(path.read_bytes()).hexdigest()
        sources.append(source)
    (args.output/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (args.output/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (args.output/'summary.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
