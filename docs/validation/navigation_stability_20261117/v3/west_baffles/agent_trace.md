# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.7 | 决策 | scan | scan_required_before_search |
| 16.6 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.7 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 19.2 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 21.1 | 决策 | explore | search_unseen_area |
| 29.6 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 29.7 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 31.3 | 决策 | scan | scan_required_before_approach |
| 46.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 47.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 48.7 | 决策 | explore | search_unseen_area |
| 65.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 65.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 67.1 | 决策 | scan | scan_required_before_approach |
| 82.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 82.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 84.3 | 决策 | explore | search_unseen_area |
| 110.4 | 工具结果 | explore / FAILED | blocked_goal |
| 110.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal |
| 112.3 | 决策 | explore | search_unseen_area |
| 115.3 | 工具结果 | explore / ABORTED | inflated_start_recovery |
| 121.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery |
| 123.1 | 决策 | explore | search_unseen_area |
| 162.6 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 162.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery; explore:FAILED:no_progress_choose_another_viewpoint |
| 164.3 | 决策 | explore | transit_to_unsearched_region |
| 182.6 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 182.7 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached |
| 184.1 | 决策 | scan | scan_required_before_approach |
| 203.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 203.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 204.9 | 决策 | scan | scan_required |
| 220.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 220.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; scan:SUCCEEDED:scan_completed |
| 221.9 | 决策 | scan | scan_uncompleted |
| 236.8 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 236.9 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:ABORTED:inflated_start_recovery; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; scan:SUCCEEDED:scan_completed; scan:SUCCEEDED:scan_completed |
| 238.4 | 决策 | report | search_exhausted |
| 238.4 | 工具结果 | report / FAILED | search_exhausted |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
