# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.6 | 决策 | scan | scan_required_before_search |
| 16.3 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.5 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 18.3 | 决策 | explore | transit_to_unsearched_region |
| 71.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 71.4 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 72.9 | 决策 | explore | search_unseen_area |
| 97.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 97.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 98.9 | 决策 | scan | scan_required_before_approach |
| 118.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 118.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 120.1 | 决策 | explore | search_unseen_area |
| 152.7 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 152.8 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 153.9 | 决策 | scan | scan_required_before_explore |
| 175.0 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 175.1 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed |
| 176.9 | 决策 | explore | transit_to_unsearched_region |
| 250.3 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 250.5 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 252.3 | 决策 | explore | transit_to_unsearched_region |
| 288.8 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 288.9 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached |
| 290.7 | 决策 | explore | search_unseen_area |
| 354.8 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 354.9 | API 请求 | ALTERNATIVE_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint |
| 356.6 | 决策 | explore | search_unseen_area |
| 398.5 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 398.9 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring |
| 400.9 | 决策 | approach | target_visible |
| 416.9 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
