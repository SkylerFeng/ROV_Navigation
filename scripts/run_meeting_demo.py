"""Launch one named recording demo; never label rule runs as LLM demonstrations."""
import argparse,json,os,subprocess,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES={
 'blue':('pool_platform_semantic_blue_search.usda','不要黄色管子，请靠近蓝色管子，距它表面保持一米。','pipe','blue',1.0),
 'yellow':('pool_platform_semantic_yellow_box_turn.usda','靠近黄色方块，不要找管子。','box','yellow',.8),
 'red':('pool_platform_semantic_red_screened.usda','请找到红色箱子，在它旁边停住。','box','red',.8),
}
def main():
 p=argparse.ArgumentParser();p.add_argument('target',choices=CASES);p.add_argument('--policy',choices=['rule','qwen','deepseek'],required=True)
 p.add_argument('--env-file',default='.env.semantic');p.add_argument('--output',type=Path);p.add_argument('--domain',type=int,default=137)
 p.add_argument('--check-config',action='store_true');a=p.parse_args()
 scene,instruction,category,color,distance=CASES[a.target]
 out=(a.output or ROOT/'logs'/('meeting_'+a.target+'_'+a.policy+'_'+datetime.now().strftime('%Y%m%d_%H%M%S'))).resolve()
 task=ROOT/'config/semantic/meeting'/f'{a.target}.json'
 cmd=[sys.executable,str(ROOT/'scripts/run_semantic_trial.py'),'--gui','--policy',a.policy,
      '--task-config',str(task),'--scene-file',str(ROOT/'scenes'/scene),'--domain',str(a.domain),'--output',str(out)]
 if a.policy!='rule':cmd+=['--env-file',a.env_file,'--instruction',instruction]
 if a.check_config:cmd+=['--check-config']
 else:
  print('Recording evidence directory: '+str(out),flush=True)
  print('Second terminal: ROS_DOMAIN_ID='+str(a.domain)+' bash scripts/start_semantic_debug.sh --save '+str(out/'debug_last.png'),flush=True)
 # Viewer stays open independently so the final status can be recorded.
 result=subprocess.run(cmd,cwd=ROOT)
 if not a.check_config and (out/'semantic/result.json').exists():
  subprocess.run([sys.executable,str(ROOT/'scripts/export_demo_stages.py'),str(out)],cwd=ROOT,check=True)
 return result.returncode
if __name__=='__main__':sys.exit(main())
