# Local plan_env overlay

Copied from the existing dependency `/home/ache/Coding/ego/ego-planner-swarm/src/planner/plan_env`, Git HEAD `23a8d5a191711dd65633df689bd00f55d4dea8f9`, origin https://github.com/ZJU-FAST-Lab/ego-planner-swarm.git . Its parent GPL-3.0 license is retained here. Local dependency tree is the ROS 2 port used by this project; no claim that it equals pristine upstream HEAD.

2026-11-17: optional `grid_map/circular_xy_inflation` in the point-cloud path. Default false preserves square inflation. Circular mode uses a circumscribed horizontal hull envelope with voxel coverage margin. Headers/class ABI are unchanged, so existing underlay optimizer libraries remain compatible. Other sensing paths retain upstream behavior.
