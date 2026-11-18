# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.5 | 决策 | scan | scan_required_before_search |
| 16.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.1 | 决策 | explore | transit_to_unsearched_region |
| 55.9 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 56.0 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 57.5 | 决策 | explore | search_unseen_area |
| 72.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 72.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 74.1 | 决策 | scan | scan_required |
| 95.5 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 95.6 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 97.3 | 决策 | explore | search_unseen_area |
| 122.6 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 122.7 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 123.9 | 决策 | scan | scan_required |
| 146.7 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 146.8 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 148.3 | 决策 | explore | transit_to_unsearched_region |
| 185.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 185.6 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 187.3 | 决策 | explore | transit_to_unsearched_region |
| 213.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 213.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 214.9 | 决策 | explore | search_unseen_area |
| 250.5 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 250.8 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring |
| 252.7 | 决策 | approach | target_visible |
| 301.3 | 工具结果 | approach / FAILED | no_progress_choose_another_viewpoint |
| 301.4 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint |
| 303.1 | 决策 | explore | search_unseen_area |
| 356.9 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 357.2 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:ABORTED:target_observed_while_exploring; approach:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring |
| 358.9 | 决策 | approach | target_visible |
| 374.9 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
