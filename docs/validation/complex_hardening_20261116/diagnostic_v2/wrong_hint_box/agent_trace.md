# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.9 | 决策 | scan | scan_required |
| 17.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 17.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 19.7 | 决策 | explore | search_unseen_area |
| 40.2 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 40.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 42.5 | 决策 | scan | scan_required |
| 65.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 65.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 68.5 | 决策 | explore | search_unseen_area |
| 98.5 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 98.6 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |
| 101.3 | 决策 | explore | search_unseen_area |
| 130.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 130.8 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached |
| 133.7 | 决策 | scan | scan_required |
| 155.1 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 155.2 | API 请求 | EXPANDED_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 158.7 | 决策 | explore | search_unseen_area |
| 192.1 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 192.2 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 195.1 | 决策 | scan | scan_required_before_explore |
| 218.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 218.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 222.3 | 决策 | explore | search_unseen_area |
| 297.3 | 工具结果 | explore / TIMEOUT | action_timeout |
| 297.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout |
| 300.5 | 决策 | explore | search_unseen_area |
| 302.4 | 工具结果 | explore / FAILED | sensor_stale_replan |
| 302.5 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan |
| 305.9 | 决策 | scan | scan_required |
| 322.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 323.0 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed |
| 326.3 | 决策 | explore | search_unseen_area |
| 346.0 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 348.0 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring |
| 351.5 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring |
| 354.9 | 决策 | approach | target_visible |
| 384.9 | 工具结果 | approach / FAILED | no_progress_choose_another_viewpoint |
| 385.0 | API 请求 | VERIFY | explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint |
| 388.5 | 决策 | approach | target_visible |
| 390.6 | 工具结果 | approach / FAILED | sensor_stale_replan |
| 390.7 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; approach:FAILED:sensor_stale_replan |
| 393.9 | 决策 | scan | scan_required_before_approach |
| 396.3 | 工具结果 | scan / SUCCEEDED | target_observed |
| 396.4 | API 请求 | VERIFY | explore:FAILED:no_progress_choose_another_viewpoint; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:TIMEOUT:action_timeout; explore:FAILED:sensor_stale_replan; scan:SUCCEEDED:scan_completed; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; approach:FAILED:sensor_stale_replan; scan:SUCCEEDED:target_observed |
| 399.7 | 决策 | approach | target_visible |
| 420.3 | 工具结果 | approach / FAILED | task_timeout |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
