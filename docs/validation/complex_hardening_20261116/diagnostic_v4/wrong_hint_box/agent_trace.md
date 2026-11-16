# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.8 | 决策 | scan | scan_initial |
| 16.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.7 | 决策 | explore | search_unseen_area |
| 39.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 40.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 41.7 | 决策 | scan | scan_required |
| 64.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 64.4 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 66.5 | 决策 | explore | search_unseen_area |
| 96.5 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 96.6 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |
| 98.6 | 决策 | explore | search_unseen_area |
| 127.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 128.0 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached |
| 130.1 | 决策 | scan | scan_required_before_approach |
| 150.8 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 150.9 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 153.5 | 决策 | explore | search_unseen_area |
| 186.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 186.2 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 188.1 | 决策 | scan | scan_required_before_explore |
| 211.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 211.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 214.1 | 决策 | explore | search_unseen_area |
| 215.2 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 215.3 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan |
| 217.7 | 决策 | scan | scan_required |
| 233.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 233.3 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed |
| 235.9 | 决策 | explore | search_unseen_area |
| 275.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 275.2 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 277.3 | 决策 | scan | scan_required |
| 296.1 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 296.2 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 298.4 | 决策 | explore | search_unseen_area |
| 370.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 370.4 | API 请求 | ALTERNATIVE_SEARCH | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 372.5 | 决策 | scan | scan_required |
| 373.6 | 工具结果 | scan / SUCCEEDED | target_observed |
| 373.7 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:target_observed |
| 375.9 | 决策 | explore | search_unseen_area |
| 420.3 | 工具结果 | explore / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
