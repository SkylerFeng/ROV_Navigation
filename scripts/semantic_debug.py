"""Read-only diagnostic payload. Cell axes are [x,y], never image [row,column]."""
import math
import numpy as np

def snapshot(node):
    g=node.grid
    cells=np.zeros(g.shape,dtype=np.uint8)
    cells[~g.inside]=1
    cells[g.free]=2
    cells[g.free & ~g.safe()]=3
    cells[g.occupied]=4
    position=None;yaw=None
    if node.odom:
        p=node.odom.pose.pose.position;q=node.odom.pose.pose.orientation
        position=[p.x,p.y,p.z]
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
    return {'sim_time':node.now(),'policy':node.args.policy,'instruction':node.cfg['instruction'],
            'state':node.mode,'reason':node.last_result,'planner_state':node.planner_state,
            'position':position,'yaw':yaw,'active':node.active,'decision':node.debug_decision,
            'objects':node.memory.observe(node.now()),'path':node.path[-2000:],
            'stages':getattr(node,'debug_stages',[]),
            'grid':{'origin':g.origin.tolist(),'resolution':g.res,'cells':cells.tolist()},
            'legend':['unknown','outside boundary','observed safe free','free but clearance blocked','occupied']}
