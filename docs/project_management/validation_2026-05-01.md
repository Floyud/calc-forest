# Validation 2026-05-01

Session: `VALIDATE-20260501-doc-consistency`

## 检查范围

- `docs/project_management/session_protocol.md`
- `docs/project_management/task_board.md`
- `docs/project_management/today_2026-05-01.md`
- `docs/product/error_taxonomy.md`
- `docs/engineering/api_plan.md`
- `docs/engineering/data_model.md`
- `docs/engineering/dify_workflow_plan.md`
- `docs/competition/创AI_开发与应用报告_草稿.md`

## 通过项

1. 教师审核边界基本一致：MVP、Dify 工作流和竞赛报告均强调 AI 输出为建议或草案，进入课堂前需要教师审核。
2. 数据脱敏边界基本一致：MVP 和数据模型使用匿名学生编号，竞赛报告也明确不采集学生敏感个人信息。
3. 核心闭环方向一致：作答记录、错因诊断、分层练习、教师摘要/讲评建议是各文档共同主线。
4. 技术路线基本一致：Dify 工作流调用 FastAPI 工具，LLM 负责解释和生成，规则/API 负责结构化诊断。

## 发现的问题

### P0 阻塞项

暂无。当前文档不影响继续搭建最小演示链路。

### P1 需要尽快修复

1. 错因编码体系不一致。
   - `docs/product/error_taxonomy.md` 使用 `E01-E11`。
   - `docs/engineering/api_plan.md`、`docs/engineering/data_model.md`、`docs/engineering/dify_workflow_plan.md` 曾使用旧版英文语义码。
   - 影响：样例数据、诊断 API、Dify 输出和教师文档无法直接对齐，后续测试会出现同一错因多套编码。

2. 首版演示题型范围不一致。
   - `today_2026-05-01.md` 建议首版覆盖三位数加减法、含 0 连续退位减法、一位数乘两位数、简单四则混合运算。
   - `docs/product/mvp_scope.md` 原先演示数据还包含小数点错误。
   - `docs/engineering/api_plan.md` 和 `dify_workflow_plan.md` 的 Demo 样例是平均分除法应用题。
   - `docs/competition/创AI_开发与应用报告_草稿.md` 的应用场景示例是分数意义单元。
   - 影响：演示数据、规则引擎和比赛叙述会分散，首版难以在有限时间内跑稳。

3. API 路径口径需要统一。
   - `today_2026-05-01.md` 提到 `POST /api/diagnose`。
   - `docs/engineering/api_plan.md` 和 Dify 工作流使用 `/api/diagnose`。
   - 影响：实现方可能按不同接口名开发。建议首版实现保留 `/api/diagnose` 为主接口，如需要兼容演示可增加 `/api/diagnose` 适配层。

### P2 建议修正

1. `data_model.md` 的 taxonomy v0.1 范围偏宽，包含分数、几何、单位换算、平均分应用题等，不适合直接作为首版计算演示的唯一标签表。
2. 竞赛报告草稿按完整系统愿景撰写，范围大于 MVP。提交前建议补充一句“当前演示版本先以整数计算错因诊断为切入点，后续扩展到分数、几何和应用题”。
3. Dify 工作流中的低置信度追问、知识库检索、练习生成是合理目标，但首版验收应先锁定结构化诊断结果是否稳定。

## 建议修复任务

1. 统一错因编码：首版规则引擎、样例数据和 Dify 输出优先使用 `E01-E11`；若需要英文码，在 API 中增加 `legacy_code` 或 `external_code` 映射，不要替代主编码。
2. 统一首版演示题型：首版只覆盖四类整数计算题型，每类至少 3 个错误样例。
3. 更新 API 与数据模型文档：把诊断响应示例中的 `primary_error_code` 改为 `E03`、`E05` 等产品标签，或明确增加编码映射表。
4. 更新 Dify Demo 样例：将平均分应用题替换为四类首版计算题中的一个，例如含 0 连续退位减法。
5. 更新竞赛报告演示口径：保留完整愿景，但把实际演示说明收窄到“整数计算错因诊断闭环”。

## 本次已处理

1. 已在 `docs/product/mvp_scope.md` 中明确首版演示题型和演示数据范围。
2. 已在 `docs/product/error_taxonomy.md` 中补充首版演示适用范围，说明哪些标签进入首版演示、哪些暂不作为首版必测。

## 实现验证补充

本轮已完成 FastAPI MVP 骨架和合成数据接入后的基础验证：

- 测试命令：`/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s development/tests/test_diagnosis.py -q`
- 测试结果：`11 passed`
- 注意事项：普通 pytest 捕获模式曾在当前环境触发临时文件 `FileNotFoundError`，关闭捕获 `-s` 后测试稳定通过。
- 合成数据：`development/data/demo_answer_records.json` 共 24 条，覆盖 5 个匿名学生编号和 3-6 年级。
- 数据字段校验：必填字段无缺失。
- 规则诊断抽查：24 条合成样例中，主错因命中任一预期标签 22 条。

当前剩余规则缺口：

1. `R0018`：括号混合运算步骤错误暂未识别，后续增强 `E05` 对括号展开和中间步骤的判断。
2. `R0021`：两位数乘法部分积错位合并暂未识别，后续增强 `E04/E08` 对部分积移位的判断。
