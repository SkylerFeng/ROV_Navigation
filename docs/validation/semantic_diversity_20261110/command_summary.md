# Qwen 指令测试（真实 API）

| 指令 | 解析结果 | 校验 | 候选动作测试 |
|---|---|---|---|
| 不要黄色管子，请靠近蓝色管子。 | accepted / blue pipe / None m | 通过 | 通过 |
| 请找到红色箱子，在它旁边停住。 | accepted / red box / None m | 通过 | 通过 |
| Find the yellow tube and stop 80 centimeters from its surface. | accepted / yellow pipe / 0.8 m | 通过 | 通过 |
| 去管子那里 | clarify / None None / None m | 通过 | 不适用 |
| 先去蓝色管子，再去红色箱子 | unsupported / None None / None m | 通过 | 不适用 |
| 去最近的黄色管子旁边 | unsupported / None None / None m | 通过 | 不适用 |
| 靠近黄色方块，不要找管子。 | accepted / yellow box / None m | 通过 | 通过 |
| 找绿色管子 | unsupported / None None / None m | 通过 | 不适用 |
| 靠近蓝色管子，距它表面保持一米。 | accepted / blue pipe / 1.0 m | 通过 | 通过 |
| 下降两米去找黄色管子 | unsupported / None None / None m | 通过 | 不适用 |

动作测试使用合成结构化观测，输入候选按协议过滤；不等同于真实环境导航。物理闭环结果单独记录。
