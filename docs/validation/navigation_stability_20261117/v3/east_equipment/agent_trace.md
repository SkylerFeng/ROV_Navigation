# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.9 | 决策 | scan | scan_initial |
| 16.9 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 17.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.7 | 决策 | explore | transit_to_unsearched_region |
| 50.2 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 50.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 52.1 | 决策 | explore | search_unseen_area |
| 96.0 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 96.1 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 98.3 | 决策 | scan | scan_required |
| 118.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 118.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 121.3 | 决策 | explore | search_unseen_area |
| 168.3 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 168.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint |
| 170.7 | 决策 | explore | search_unseen_area |
| 193.3 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 194.5 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring |
| 197.1 | 决策 | approach | target_visible |
| 237.4 | 工具结果 | approach / FAILED | no_progress_choose_another_viewpoint |
| 237.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint |
| 240.1 | 决策 | explore | search_unseen_area |
| 262.8 | 工具结果 | explore / ABORTED | inflated_start_recovery |
| 271.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:inflated_start_recovery |
| 274.1 | 决策 | explore | search_unseen_area |
| 319.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 320.9 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:inflated_start_recovery; explore:ABORTED:target_observed_while_exploring |
| 323.5 | 决策 | approach | target_visible |
| 357.5 | 工具结果 | approach / FAILED | local_recovery_started |
| 358.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:inflated_start_recovery; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started |
| 361.1 | 决策 | approach | target_visible |
| 407.1 | 工具结果 | approach / FAILED | verification_failed_reobserve_locally |
| 407.2 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:inflated_start_recovery; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started; approach:FAILED:verification_failed_reobserve_locally |
| 409.7 | 决策 | approach | target_visible |
| 419.1 | 工具结果 | approach / ABORTED | target_position_updated |
| 419.2 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:inflated_start_recovery; explore:ABORTED:target_observed_while_exploring; approach:FAILED:local_recovery_started; approach:FAILED:verification_failed_reobserve_locally; approach:ABORTED:target_position_updated |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
