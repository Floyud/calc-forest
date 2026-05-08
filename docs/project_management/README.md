# Project Management Hub

这个目录用于管理跨 Codex session 的推进节奏，解决两个问题：

1. 新 session 打开后，能快速知道现在项目在哪里、下一步该做什么。
2. 把不同 session 分成 **exploration** 和 **exploitation**，避免一边探索一边随意改核心实现。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `session_protocol.md` | 每次开启 Codex session 时先读的工作协议 |
| `task_board.md` | 长期任务板，按 exploration / exploitation / validation 分组 |
| `today_2026-05-01.md` | 今天能做的具体任务与完成标准 |
| `decision_log.md` | 关键产品与技术决策记录 |

## Session 类型

### Exploration

目标是把未知问题弄清楚，通常不直接写实现代码。

适合任务：

- 研究 Coze / Dify / Qwen-Agent / OCR / 题库生成方案。
- 阅读竞赛指南、政策、课程标准。
- 梳理需求、用户流程、数据结构。
- 做小规模技术验证，但不把验证代码直接当产品实现。

输出要求：

- 写入研究结论或决策建议。
- 标明推荐方案、备选方案、风险和下一步 exploitation 任务。

### Exploitation

目标是把已经明确的方案做出来，并做得可演示、可测试、可复现。

适合任务：

- 写 FastAPI 服务。
- 实现诊断规则引擎。
- 搭 Dify 工作流。
- 写测试与演示数据。
- 完成页面、脚本、报告、视频素材。

输出要求：

- 列出改动文件。
- 给出验证命令或验证结果。
- 更新 `task_board.md` 中对应任务状态。

### Validation

目标是检查已经完成的东西是否能用于比赛材料或下一阶段开发。

适合任务：

- 跑测试。
- 检查文档一致性。
- 复核隐私合规。
- 演示流程彩排。
- 检查是否符合《创AI》提交规范。

## 新 session 推荐启动顺序

1. 读 `docs/project_management/session_protocol.md`。
2. 读 `docs/project_management/task_board.md`。
3. 如果是当天继续推进，读当天计划文件。
4. 明确本次 session 类型：exploration / exploitation / validation。
5. 只做本次 session 类型匹配的任务。
6. 结束前更新任务板和决策记录。
