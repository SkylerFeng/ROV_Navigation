# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.9 | 决策 | scan | scan_required |
| 17.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 17.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 19.7 | 决策 | explore | search_unseen_area |
| 40.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 40.2 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 42.3 | 决策 | scan | scan_required |
| 64.5 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 64.6 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 67.4 | 决策 | explore | search_unseen_area |
| 116.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 117.0 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 120.0 | 决策 | scan | scan_required |
| 143.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 143.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 147.3 | 决策 | explore | search_unseen_area |
| 185.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 185.6 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 188.6 | 决策 | scan | scan_required_before_explore |
| 212.8 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 212.9 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 216.3 | 决策 | explore | search_unseen_area |
| 240.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 241.0 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 243.8 | 决策 | scan | scan_required_before_explore |
| 268.1 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 268.2 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 271.5 | 决策 | explore | search_unseen_area |
| 293.4 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 293.5 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 296.1 | 决策 | scan | scan_uncompleted |
| 346.1 | 工具结果 | scan / TIMEOUT | bounded_scan_finished |
| 346.2 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:TIMEOUT:bounded_scan_finished |
| 348.9 | 决策 | explore | search_unseen_area |
| 350.4 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 350.5 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:TIMEOUT:bounded_scan_finished; explore:FAILED:sensor_stale_replan |
| 353.1 | 决策 | scan | scan_required |
| 358.1 | 工具结果 | scan / SUCCEEDED | target_observed |
| 358.2 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:TIMEOUT:bounded_scan_finished; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed |
| 361.1 | 决策 | approach | target_visible |
| 391.1 | 工具结果 | approach / FAILED | no_progress_choose_another_viewpoint |
| 391.3 | API 请求 | GLOBAL_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:TIMEOUT:bounded_scan_finished; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed; approach:FAILED:no_progress_choose_another_viewpoint |
| 394.1 | 决策 | explore | search_unseen_area |
| 420.3 | 工具结果 | explore / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
