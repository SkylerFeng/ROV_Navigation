# EGO simulation-clock overlay

`src/plan_manage` is copied from the user's existing
`/home/ache/Coding/ego/ego-planner-swarm/src/planner/plan_manage`, upstream commit
`23a8d5a191711dd65633df689bd00f55d4dea8f9` (any local modifications are preserved).
The supplied GPL license is retained. The original checkout is not edited.

The project overlay changes trajectory/FSM timing to the node's clock:

- Planner manager stores `node->get_clock()` instead of constructing system clocks.
- FSM uses `node_->now()` for trajectory progress and stamps.
- Trajectory server uses its node's ROS clock and skips callbacks when `/clock`
  has not advanced, avoiding division by zero in yaw updates.

This makes `use_sim_time=true` effective when simulation runs faster/slower
than wall time. Wall timers still service callbacks; trajectory progress uses
simulation time.

Build with `bash scripts/build_planner.sh` from the project root. The navigation
launcher sources the original underlay followed by this overlay. It does not
launch the original UAV simulator.


The ROV adaptation also checks measured tracking deviation (`fsm/max_tracking_error`),
holds and replans from measured odometry, and uses actual goal distance for completion.
An observed occupied goal enters `BLOCKED_GOAL`; a replacement goal starts planning
without a nested spin/wait inside its callback. `/rov/planner_status` exposes these states.
Trajectory-server ROS entities are released before process teardown.

Regression: `scripts/test_planner_feedback.py` verifies occupied-goal handling,
replacement-goal responsiveness and absence of arrival inferred only from nominal time.


Heading-aware execution (enabled together in `scripts/navigation.launch.py`):

- `fsm/heading_aware_execution` holds the local spline phase while the required
  translation direction lies outside `fsm/max_heading_error_deg`. The local
  trajectory epoch is shifted by the held interval, keeping recovery, replanning
  and collision prediction consistent. Routine replanning waits during alignment;
  map updates, safety checks and new goals remain active.
- `/rov/trajectory_phase` (`geometry_msgs/Vector3Stamped`) is the authoritative
  phase heartbeat: x = trajectory ID, y = elapsed spline seconds, z = 0 while
  heading-paused, otherwise 1; header stamp uses simulation time.
- `traj_server/use_execution_phase` samples only the matching phase. A stale
  (>0.5 s) or unmatched heartbeat holds position with zero reference velocity.
  The wall/ROS simulation clock itself is never paused.
- A local guide endpoint inside the inflated map is extended to a free point
  along the global guide; EGO still must optimize and check the connecting path.
- The phase mechanism targets this single-ROV static-obstacle experiment. It is
  not a swarm-wide time-rescheduling protocol.

Regressions: `test_clock.py --execution-phase` verifies phase hold/resume and
stale-heartbeat holding; `test_heading_execution.py` runs the real planner to
check heading holds without recovery loops, resumption and replacement goals.
Both features default off in the standalone C++ binaries for legacy clock tests.

Observed global guide (`fsm/observed_global_guide`): a fixed-height 0.1 m A*
search on the actual depth-derived inflated map, with a soft cost near
occupied cells. Edges are sampled every 0.025 m; shortcuts are checked with
additional lateral margin. Guide waypoints seed the existing EGO global
polynomial; EGO remains responsible for local B-spline optimization and
collision validation. The known water polygon in config/pool_water_boundary.json
constrains guide search with a 0.4 m hull allowance. It contains no obstacle
positions; unobserved cells retain the map's existing free/unknown convention.
`test_observed_guide.cpp` covers detours, blocked starts, disconnected maps
and collision-free guide segments. This guide does not imply complete perception.


2026-10-15 turn recurrence fix: the Python tracker and FSM use the actual
translation direction down to 1e-6 m/s, without a low-speed fallback to spline
yaw. Local targets follow the visible prefix of the observed A* polyline
instead of skipping corners on its polynomial fit. Failed GEN_NEW_TRAJ
attempts are bounded to one per 0.5 simulation seconds. Expired final
trajectories that miss the real goal request a fresh plan.
Within 0.2 m of the goal and below 0.05 m/s, an exact terminal B-spline
can be generated; it preserves initial position/velocity, has zero terminal
velocity/acceleration, and is checked at 0.01 s intervals against occupancy
and velocity/acceleration limits. The real planner regression verifies a
0.1 m terminal target and absence of completion with stationary odometry.
