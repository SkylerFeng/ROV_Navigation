"""Preserve actual agent tool feedback, navigation audit and final sensor evidence."""
import argparse,json,shutil,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from analyze_semantic_trial import analyze
from analyze_navigation_motion import analyze as motion

def package(run,output):
    audit=analyze(run,output);motion(run,output/'motion')
    diagnostics=run/'semantic/diagnostics'
    if diagnostics.exists():shutil.copytree(diagnostics,output/'semantic/diagnostics',dirs_exist_ok=True)
    for name in ['semantic/events.jsonl','semantic/result.json','semantic/agent_memory.json','instruction.json','manifest.json','config/agent.json','config/vision.json','config/task.json','config/runtime.json','config/experiment.json','sim/run.json']:
        p=run/name
        if p.exists():
            dst=output/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    with np.load(run/'semantic/latest_sensor.npz') as d:
        Image.fromarray(d['rgb']).save(output/'last_detector_input.png')
        Image.fromarray(d['raw_rgb'] if 'raw_rgb' in d.files else d['rgb']).save(output/'last_camera_raw.png')
    events=[json.loads(x) for x in (run/'semantic/events.jsonl').read_text().splitlines()]
    trace=[]
    for e in events:
        if e['event']=='llm_request':
            obs=e['observation'];mem=obs.get('agent_memory')
            trace.append({'sim_time':e['sim_time'],'event':'llm_request','observation_id':obs['observation_id'],'agent_memory':mem})
        elif e['event'] in ('agent_tool_started','agent_tool_result','agent_motion_loop','agent_search_expanded','target_local_refinement','decision_superseded_by_target','result','decision'):
            trace.append({k:v for k,v in e.items() if k not in ('observation','path','last_objects')})
    (output/'agent_trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2)+'\n')
    lines=['# Agent 实际执行与反馈','','| 仿真秒 | 事件 | 动作/结果 | 反馈 |','|---:|---|---|---|']
    for e in trace:
        if e['event']=='llm_request':
            m=e.get('agent_memory') or {};detail='; '.join(r['action']+':'+r['status']+':'+r['reason'] for r in m.get('recent_results',[]))
            lines.append(f"| {e['sim_time']:.1f} | API 请求 | {m.get('phase','旧接口')} | {detail} |")
        elif e['event']=='agent_tool_result':lines.append(f"| {e['sim_time']:.1f} | 工具结果 | {e['action']} / {e['status']} | {e['reason']} |")
        elif e['event']=='decision':lines.append(f"| {e['sim_time']:.1f} | 决策 | {e['action']['action']} | {e['action']['reason_code']} |")
    lines+=['','这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。']
    (output/'agent_trace.md').write_text('\n'.join(lines)+'\n')
    sources=[run/'semantic/events.jsonl',run/'semantic/latest_sensor.npz',run/'sim/run.json',run/'manifest.json']
    (output/'sources.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
    return audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();package(a.run,a.output)
