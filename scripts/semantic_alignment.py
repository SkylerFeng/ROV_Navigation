"""Path-entry heading for a bounded rotation shim, using observed free space."""
import math

def entry_heading(grid,position,goal,lookahead=.6):
    costs,parents=grid.reachable(position);end=grid.cell(goal)
    if end not in costs:return None
    route=[end]
    while route[-1] in parents:route.append(parents[route[-1]])
    route.reverse()
    step=next((c for c in route if costs.get(c,0)>=lookahead),end)
    point=grid.xy(step)
    return math.atan2(point[1]-position[1],point[0]-position[0])
