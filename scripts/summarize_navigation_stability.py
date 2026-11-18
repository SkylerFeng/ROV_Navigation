"""Offline comparison only. Report failures and alignment episodes as well as success."""
import argparse,json
from pathlib import Path

def summarize(run):
    events=[json.loads(l) for l in (run/'semantic/events.jsonl').read_text().splitlines()]
    result=json.loads((run/'semantic/result.json').read_text())
    physical=json.loads((run/'sim/run.json').read_text())
    contacts=physical.get('contacts',[])
    episodes=[];start=None;last=None
    for e in events:
        if e['event']!='tracking':continue
        t=e['sim_time']
        if e.get('mode')=='ALIGNING':
            if start is None:start=t
            last=t
        elif start is not None:
            episodes.append(last-start);start=None
    if start is not None:episodes.append(last-start)
    align_start=None;entry_durations=[]
    for e in events:
        if e['event']=='navigation_entry_alignment':align_start=e['sim_time']
        if e['event']=='navigation_entry_aligned' and align_start is not None:
            entry_durations.append(e['sim_time']-align_start);align_start=None
    return {'entry_alignment_durations_s':entry_durations,'run':str(run),'status':result['status'],'reason':result['reason'],
        'simulation_seconds':result['simulation_seconds'],'llm_calls':result['llm_calls'],
        'contacts':len(contacts),'physical_contact_pairs':sum(c.get('min_separation_m',1)<0 or c.get('max_impulse_norm',0)>0 for c in contacts),
        'action_timeouts':sum(e['event']=='agent_tool_result' and e.get('reason')=='action_timeout' for e in events),
        'stale_phase_samples':sum(e['event']=='tracking' and e.get('mode')=='STALE_PHASE' for e in events),
        'semantic_stale_samples':sum(e['event']=='tracking' and e.get('mode')=='SEMANTIC_STALE' for e in events),
        'no_progress_events':sum(e['event']=='navigation_no_progress' for e in events),
        'spin_guard_events':sum(e['event']=='agent_motion_loop' for e in events),
        'category_conflict_aborts':sum(e['event']=='approach_category_conflict' for e in events),
        'blocked_tools':sum(e['event']=='agent_tool_result' and e.get('reason')=='blocked_goal' for e in events),
        'max_alignment_episode_s':max(episodes,default=0),
        'alignment_sample_span_total_s':sum(episodes),
        'region_switches':[e for e in events if e['event']=='agent_search_expanded'],
        'limitations':'Sampled tracking log; alignment is not necessarily a spin failure; contact pairs use raw PhysX reports. Older versions did not expose STALE_PHASE explicitly, so zero old samples cannot prove no stale phase. No statistical success claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directories',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rows=[summarize(r) for r in a.directories]
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k!='region_switches'} for row in rows],indent=2))
