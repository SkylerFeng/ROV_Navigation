# Agent 实际执行与反馈

| 仿真秒 | 事件 | 动作/结果 | 反馈 |
|---:|---|---|---|
| 0.3 | API 请求 | 旧接口 |  |
| 2.9 | 决策 | scan | scan_required |
| 18.3 | API 请求 | 旧接口 |  |
| 20.9 | 决策 | explore | search_unseen_area |
| 31.3 | API 请求 | 旧接口 |  |
| 33.7 | 决策 | scan | scan_required |
| 47.4 | API 请求 | 旧接口 |  |
| 50.5 | 决策 | approach | target_visible |

这份记录证明反馈被送入后续请求，不能单凭请求内容证明 LLM 的内部因果推理或性能提升。相机为末次保存快照。
