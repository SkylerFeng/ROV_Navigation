"""Package completed complex trials with honest success/failure metrics."""
import argparse,json,contextlib,io,shutil
from pathlib import Path
from package_agent_validation import package
from plot_complex_semantic import plot

def main():
    p=argparse.ArgumentParser();p.add_argument('runs',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
    cases=json.loads(Path('config/semantic/complex_suite.json').read_text())
    for c in cases:
        run=a.runs/c['name'];out=a.output/c['name']
        if not (run/'semantic/result.json').exists():continue
        with contextlib.redirect_stdout(io.StringIO()):audit=package(run,out)
        events=[json.loads(l) for l in (run/'semantic/events.jsonl').read_text().splitlines()]
        row={k:audit.get(k) for k in ['runtime_status','reason','simulation_seconds','path_length_m','contact_pairs','contact_evidence','offline_verified','exploration_verified','target_initially_detected','llm_calls','final_target_surface_distance_xy_m']}
        row['name']=c['name'];row['search_expansions']=[{k:e.get(k) for k in ('sim_time','expansion','global_search')} for e in events if e['event']=='agent_search_expanded']
        row['superseded_search_decisions']=sum(e['event']=='decision_superseded_by_target' for e in events)
        row['local_refinements']=sum(e['event']=='target_local_refinement' for e in events)
        row['llm_rejections']=sum(e['event']=='llm_error' for e in events)
        row['recovery_events']=sum(e['event']=='recovery_started' for e in events)
        row['scan_seconds']=sum(e.get('duration_s',0) for e in events if e['event']=='agent_tool_result' and e.get('action')=='scan')
        row['navigation_spin_events']=sum(e['event']=='agent_motion_loop' for e in events)
        row['first_target_detection_s']=next((e['sim_time'] for e in events if any(d['category']==audit['target']['category'] and d['color']==audit['target']['color'] for d in e.get('detections',[]))),None)
        rows.append(row)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    plot(a.output,a.runs)
    lines=['# 复杂场景真实导航结果','','使用真实 Qwen API + Isaac Sim。表中时间为仿真秒，路径为实际测量；失败也保留。','','| 场景 | 状态 | 时间s | 航程m | 接触对 | 离线审核 | 初始不可见且通过 |','|---|---|---:|---:|---:|---|---|']
    for r in rows:lines.append(f"| {r['name']} | {r['runtime_status']} | {r['simulation_seconds']:.1f} | {r['path_length_m']:.2f} | {r['contact_pairs']} | {r['offline_verified']} | {r['exploration_verified']} |")
    lines+=['','[布局与实测轨迹](complex_scenes.png)。每个场景子目录保留 `trajectory.png`、`last_camera_raw.png`、`latest_detection.jpg`、`agent_trace.md`、`audit.json` 和事件日志。',
            '','`summary.json` 另外记录首次目标检测时间、区域扩展、API 决策拒绝、原地转圈保护及局部位置更新次数。',
            '','每组仅一次，不能估算成功率或证明区域提示提高效率；三种布局不构成同场景有无先验的消融实验。相机定位依赖理想距离和真实位姿。',
            '','`layout_checks.json` 仅为离线平面连通性预检查，不替代物理碰撞审核。实跑为 headless 相机渲染，未做 GUI 录像验收。']
    (a.output/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
