"""Package completed Qwen task evidence without rerunning inference or hiding failures."""
import argparse,csv,hashlib,json,shutil,contextlib,io
from pathlib import Path
import numpy as np
from PIL import Image
from analyze_semantic_trial import analyze
from analyze_navigation_motion import analyze as motion
from export_demo_stages import export

def package(suite,output):
 output.mkdir(parents=True,exist_ok=True);rows=[]
 for case in json.loads(suite.read_text()):
  run=Path(case['run']);dest=output/case['name'];dest.mkdir(exist_ok=True)
  row={'name':case['name'],'instruction':case['instruction'],'run':str(run)}
  try:
   with contextlib.redirect_stdout(io.StringIO()):
    audit=analyze(run,dest);motion(run,dest/'motion');export(run)
   row.update(status=audit['runtime_status'],reason=audit['reason'],strict_pass=audit['offline_verified'],seconds=audit['simulation_seconds'],path_m=audit['path_length_m'],contact_pairs=audit['contact_pairs'],decision_calls=audit['llm_calls'],surface_distance_m=audit['final_target_surface_distance_xy_m'])
   shutil.copytree(run/'presentation',dest/'stages',dirs_exist_ok=True)
   result=json.loads((run/'semantic/result.json').read_text())
   with (dest/'measured_trajectory.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['sim_time_s','x_m','y_m','z_m']);w.writerows(result['path'])
  except (ValueError,FileNotFoundError,KeyError) as exc:
   row.update(status='INCOMPLETE',reason=str(exc),strict_pass=False)
  for f in ['instruction.json','summary.json','manifest.json','semantic/result.json','semantic/events.jsonl','config/task.json','config/runtime.json','config/experiment.json','semantic/map.npz','sim/run.json','sim/plans.json','sim/controls.json','sim/scene_evidence.json']:
   source=run/f
   if source.exists():target=dest/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
  sensor=run/'semantic/latest_sensor.npz'
  if sensor.exists():
   with np.load(sensor) as d:Image.fromarray(d['rgb']).save(dest/'last_camera_rgb.png')
   events=[json.loads(l) for l in (run/'semantic/events.jsonl').read_text().splitlines()]
   last=next((e for e in reversed(events) if e['event']=='perception'),None)
   row['last_snapshot_event_sim_s']=last['sim_time'] if last else None
   (dest/'camera_metadata.json').write_text(json.dumps({'source':str(sensor),'snapshot_event_sim_s':row['last_snapshot_event_sim_s'],'note':'Last saved RGB snapshot, nominal 2s interval; event timestamp is processing time, not exact camera exposure or terminal frame. Detection overlay is original saved pipeline output, not re-inference.'},indent=2)+'\n')
  rows.append(row)
  notes=[f"# {case['name']}",'',case['instruction'],'',f"状态：{row['status']}；严格离线通过：{row['strict_pass']}",f"原因：{row['reason']}；接触物体对数：{row.get('contact_pairs', '未知')}（非接触次数）",'','- trajectory.png：实测轨迹（目标真值仅离线标注）。','- last_camera_rgb.png：最后保存的相机原图。','- latest_detection.jpg：与快照对应的原始检测叠加图。','- stages/stages.md：实际执行的决策/恢复事件。','- semantic/events.jsonl：包含API请求、返回、拒绝与执行的完整记录。','- motion/motion.png：速度和转向曲线。','','快照不是保证成功的一帧，也不保证为仿真结束的最后曝光帧；失败状态应一并展示。缺失文件表示该次未生成。']
  (dest/'README.md').write_text('\n'.join(notes)+'\n')
 # Ready-to-use presentation pages, retaining task and outcome on each image.
 import matplotlib.pyplot as plt
 from matplotlib.backends.backend_pdf import PdfPages
 from semantic_debug_viewer import configure_fonts
 configure_fonts()
 with PdfPages(output/'report_slides.pdf') as pdf:
  for row in rows:
   dest=output/row['name'];fig=plt.figure(figsize=(16,9))
   grid=fig.add_gridspec(2,2,width_ratios=[1.25,1])
   axes=[fig.add_subplot(grid[:,0]),fig.add_subplot(grid[0,1]),fig.add_subplot(grid[1,1])]
   for ax,filename,title in zip(axes,['trajectory.png','last_camera_rgb.png','latest_detection.jpg'],['实测轨迹（真值目标仅用于离线审核）','最后保存的相机原图','最后保存的检测结果']):
    ax.axis('off');image=dest/filename
    if image.exists():ax.imshow(plt.imread(image))
    else:ax.text(.1,.5,'无已保存图像',transform=ax.transAxes)
    ax.set_title(title,fontsize=12)
   fig.suptitle(row['instruction']+'\n'+f"Qwen | {row['status']} | 离线审核: {row['strict_pass']} | 接触对数: {row.get('contact_pairs','?')} | {row.get('seconds',0):.1f}s | {row.get('path_m',0):.2f}m",fontsize=16)
   fig.text(.02,.02,'真实Qwen + YOLO + A*/EGO + 部件水动力；单次headless运行，不代表成功率。相机为最后已保存快照。',fontsize=10)
   fig.subplots_adjust(left=.02,right=.98,bottom=.08,top=.82,hspace=.35,wspace=.08);fig.savefig(dest/'report_slide.png',dpi=150);pdf.savefig(fig);plt.close(fig)
 (output/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 with (output/'summary.csv').open('w') as f:
  fields=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 lines=['# 组会材料：三条真实Qwen指令','','本批为真实Qwen API + YOLO + A*/EGO + 部件水动力，headless实际渲染相机；无规则回退。每任务一次，不是成功率统计。','','| 任务 | 指令 | 结果 | 严格审核 | 仿真秒 | 航程m |','|---|---|---|---|---:|---:|']
 for r in rows:lines.append(f"| [{r['name']}]({r['name']}/README.md) | {r['instruction']} | {r['status']} | {r['strict_pass']} | {r.get('seconds',0):.1f} | {r.get('path_m',0):.2f} |")
 lines+=['','直接用于PPT：[三页汇报PDF](report_slides.pdf)。每个任务目录的 report_slide.png 为对应单页图片；stages/stages.md 为决策时间线。','','统计口径：时间为仿真时间；decision_calls 是运行中决策调用，不包含启动时的指令解析。停靠距离为 ROV 参考位置到目标水平表面的距离，检测图标注为相机测距，两者不等价。定位使用仿真深度和真值位姿，尚未验证真实传感器误差。','','录屏版与本次headless运行调度条件不同，不能据此保证GUI复现结果。默认膨胀0.25m，不使用实验转向加速。相机为最后保存的快照，见各任务camera_metadata.json；不隐去失败、碰撞或定位偏差。','']
 (output/'README.md').write_text('\n'.join(lines))
 sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for case in json.loads(suite.read_text()) for p in Path(case['run']).rglob('*') if p.is_file() and p.suffix in ['.json','.jsonl','.npz']}
 (output/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
 print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('suite',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();package(a.suite,a.output)
