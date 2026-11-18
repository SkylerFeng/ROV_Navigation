# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.7 | 决策 | scan | scan_required_before_search |
| 16.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.5 | 决策 | explore | transit_to_unsearched_region |
| 61.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 61.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 63.1 | 决策 | explore | search_unseen_area |
| 82.0 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 82.1 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 83.7 | 决策 | scan | scan_required |
| 105.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 105.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 107.3 | 决策 | explore | search_unseen_area |
| 182.3 | 工具结果 | explore / TIMEOUT | action_timeout |
| 182.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout |
| 184.3 | 决策 | explore | search_unseen_area |
| 235.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 235.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached |
| 237.3 | 决策 | scan | scan_uncompleted |
| 258.6 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 258.7 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 260.9 | 决策 | explore | transit_to_unsearched_region |
| 311.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 311.6 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 313.7 | 决策 | explore | transit_to_unsearched_region |
| 314.6 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 314.7 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:sensor_stale_replan |
| 316.5 | 决策 | scan | scan_required |
| 332.0 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 332.1 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed |
| 334.1 | 决策 | explore | search_unseen_area |
| 409.1 | 工具结果 | explore / TIMEOUT | action_timeout |
| 409.3 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout |
| 411.1 | 决策 | explore | transit_to_unsearched_region |
| 420.3 | 工具结果 | explore / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
