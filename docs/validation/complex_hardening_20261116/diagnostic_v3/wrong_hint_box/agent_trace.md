# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.8 | 决策 | scan | scan_initial |
| 16.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.7 | 决策 | explore | search_unseen_area |
| 39.8 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 39.9 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 41.7 | 决策 | scan | scan_required |
| 64.4 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 64.5 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 66.7 | 决策 | explore | search_unseen_area |
| 96.7 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 96.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |
| 98.6 | 决策 | explore | search_unseen_area |
| 128.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 128.4 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached |
| 130.5 | 决策 | scan | scan_required_before_explore |
| 150.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 151.0 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 153.6 | 决策 | explore | search_unseen_area |
| 186.4 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 186.5 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 188.9 | 决策 | scan | scan_required_before_explore |
| 212.5 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 212.6 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 215.1 | 决策 | explore | search_unseen_area |
| 282.8 | 工具结果 | explore / FAILED | blocked_goal |
| 282.9 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal |
| 285.4 | 决策 | explore | search_unseen_area |
| 301.3 | 工具结果 | explore / FAILED | blocked_goal |
| 301.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal |
| 303.7 | 决策 | explore | search_unseen_area |
| 305.7 | 工具结果 | explore / FAILED | blocked_goal |
| 305.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal |
| 308.1 | 决策 | explore | search_unseen_area |
| 338.1 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 338.2 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint |
| 340.5 | 决策 | explore | search_unseen_area |
| 342.5 | 工具结果 | explore / FAILED | blocked_goal |
| 342.6 | API 请求 | ALTERNATIVE_SEARCH | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal |
| 344.9 | 决策 | explore | search_unseen_area |
| 350.2 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 350.3 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal; explore:FAILED:sensor_stale_replan |
| 352.9 | 决策 | scan | scan_uncompleted |
| 354.0 | 工具结果 | scan / SUCCEEDED | target_observed |
| 354.1 | API 请求 | VERIFY | explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed |
| 356.5 | 决策 | explore | search_unseen_area |
| 369.8 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 369.9 | API 请求 | ALTERNATIVE_SEARCH | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed; explore:FAILED:sensor_stale_replan |
| 372.2 | 决策 | scan | scan_uncompleted |
| 387.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 387.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed |
| 390.1 | 决策 | explore | search_unseen_area |
| 420.1 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 420.2 | API 请求 | ALTERNATIVE_SEARCH | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:blocked_goal; explore:FAILED:no_progress_choose_another_viewpoint; explore:FAILED:blocked_goal; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
