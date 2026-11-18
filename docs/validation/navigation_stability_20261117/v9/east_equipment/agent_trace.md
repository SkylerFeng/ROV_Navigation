# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | REGION_SEARCH |  |
| 1.5 | 决策 | scan | scan_required_before_explore |
| 16.2 | 工具结果 | scan / SUCCEEDED | scan_completed |
| 16.3 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed |
| 17.9 | 决策 | explore | transit_to_unsearched_region |
| 55.5 | 工具结果 | explore / SUCCEEDED | exploration_waypoint_reached |
| 55.6 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached |
| 56.9 | 决策 | explore | search_unseen_area |
| 116.8 | 工具结果 | explore / FAILED | no_progress_choose_another_viewpoint |
| 116.9 | API 请求 | REGION_SEARCH | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint |
| 118.3 | 决策 | explore | search_unseen_area |
| 148.1 | 工具结果 | explore / ABORTED | target_observed_while_exploring |
| 148.4 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring |
| 150.3 | 决策 | approach | target_visible |
| 168.6 | 工具结果 | approach / FAILED | blocked_goal |
| 168.8 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:blocked_goal |
| 170.3 | 决策 | approach | target_visible |
| 174.1 | 工具结果 | approach / FAILED | blocked_goal |
| 174.2 | API 请求 | VERIFY | scan:SUCCEEDED:scan_completed; explore:SUCCEEDED:exploration_waypoint_reached; explore:FAILED:no_progress_choose_another_viewpoint; explore:ABORTED:target_observed_while_exploring; approach:FAILED:blocked_goal; approach:FAILED:blocked_goal |
| 175.7 | 决策 | approach | target_visible |
| 200.9 | 工具结果 | approach / SUCCEEDED | visual_identity_range_heading_and_hold_verified |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
