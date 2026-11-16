"""Export actual accepted decisions/recoveries as a presentation timeline."""
import argparse,csv,json
from pathlib import Path

def export(directory):
 source=directory/'semantic/events.jsonl';rows=[]
 for line in source.read_text().splitlines():
  e=json.loads(line);kind=e['event']
  if kind=='decision':
   a=e['action'];obs=e['observation'];candidate=next((c for c in obs['candidates'] if c['id']==a.get('candidate_id')),None)
   rows.append([e['sim_time'],'decision',a['action'],a['reason_code'],a.get('object_id',''),json.dumps(candidate.get('position') if candidate else None)])
  elif kind in ('recovery_started','navigation_no_progress','verification_failed','result'):
   rows.append([e['sim_time'],kind,e.get('status',e.get('mode','')),e.get('reason',''),e.get('object_id',''),''])
 out=directory/'presentation';out.mkdir(exist_ok=True)
 with (out/'stages.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['sim_time_s','event','action_or_state','reason','object_id','waypoint']);w.writerows(rows)
 text=['# 实际运行阶段记录','','时间为仿真秒，不直接等同于录屏时间。保留失败与恢复，不代表所有阶段成功。','', '| 仿真秒 | 事件 | 动作/状态 | 原因 |','|---:|---|---|---|']
 for t,event,action,reason,_,_ in rows:text.append(f'| {t:.1f} | {event} | {action} | {reason} |')
 (out/'stages.md').write_text('\n'.join(text)+'\n')
 print(out/'stages.md')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);export(p.parse_args().directory)
