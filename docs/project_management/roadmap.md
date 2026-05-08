# 我的计算森林 — 功能演进路线图

> 维护方式：`[ ]` 未完成，`[x]` 已完成。每完成一项即时更新。

---

## 阶段一：数据基础层（SQLite + 实体模型）

- [x] 引入 `aiosqlite` 依赖，建立数据库连接管理（`development/app/db.py`）
- [x] 设计并创建表结构：`students`、`classes`、`academic_cycles`、`diagnosis_history`、`student_cycle_progress`
- [x] 新增 Pydantic 模型：`Student`、`StudentProfile`、`Class`、`AcademicCycle`、`StudentCycleProgress`
- [x] 建种子数据脚本：1 个班级（四年级2班）、10 个学生、2025-2026 学年日历（上学期 + 下学期 + 寒暑假）
- [x] 实现 Student CRUD service + API 端点（`GET /api/students/{id}`、`GET /api/students/{id}/profile`）
- [x] 实现 Class CRUD service + API 端点（`GET /api/classes/{id}`、`GET /api/classes/{id}/summary`）
- [x] 实现 AcademicCycle 查询 service + API 端点（`GET /api/cycles/current?grade=`）
- [x] 迁移现有 `demo_answer_records.json` 到 SQLite `diagnosis_history` 表

## 阶段二：后端编排模式重构（Dify-style Pipeline）

- [x] 设计 Pipeline Node 接口（`BaseNode`：execute、input_schema、output_schema）
- [x] 实现轻量 Pipeline 编排器（node 注册、顺序执行、条件分支、失败即停）
- [x] 将 `diagnosis.py` 重构为 `DiagnosisNode`
- [x] 将 `practice.py` 重构为 `PracticeNode`
- [x] 新增 `GrowthConfigNode`（树种 + 鼓励语配置查询）
- [x] 新增 `ProfileUpdateNode`（批阅后自动持久化到 diagnosis_history）
- [x] 新增 `GrowthUpdateNode`（记录练习天数 + 推进里程碑）
- [x] 将 `session_draft.py` 改为 Pipeline 组装模式
- [x] 提取 `response_assembler.py` 消除重复代码
- [x] 提取 `student_feedback_builder.py` 纯函数
- [x] 新增 `POST /api/dify/full-pipeline` 端点（含持久化 + 成长记录）

## 阶段三：作业生命周期

- [x] 设计 `homework`、`homework_problems`、`homework_submissions`、`student_answers` 表
- [x] 实现 `HomeworkGenNode`：基于班级/学生画像生成个性化作业
- [x] `POST /api/homework/generate` — 生成作业
- [x] `POST /api/homework/assign` — 分发作业
- [x] `POST /api/homework/submit` — 学生提交答案（模拟）
- [x] `POST /api/homework/grade` — 自动批阅 + 诊断 + 更新画像
- [x] 作业模拟器：10 个学生"假装作答"
- [x] `GET /api/students/{id}/profile` 完整版（含历史错因分布、准确率趋势）

## 阶段四：校历与成长系统

- [x] 创建标准中国公立小学校历配置（2025-2026 学年）
- [x] `GET /api/cycles/current` 查询当前周期
- [x] `GET /api/students/{id}/growth` 查看成长进度
- [x] `POST /api/growth/record-practice` 记录练习 + 推进里程碑（通过 full-pipeline 自动触发）
- [x] 9 阶段里程碑自动计算
- [x] 鼓励语匹配逻辑完善（最近规则匹配）

## 阶段五：轻量知识库

- [x] 按错因码拆分知识库文件（`taxonomy/E02_carry.md`、`E03_borrow.md`、`E05_operation_order.md`）
- [x] 作业模板文件（`homework_templates/E03_grade4.md`）
- [x] SQLite FTS5 全文索引
- [x] `GET /api/knowledge/search?q=...` 后端查询端点
- [x] 补全错因文档：E01 基础事实、E04 数位对齐、E07 抄题转写、E08 步骤遗漏、E11 未验算
- [x] 补全作业模板：E01/E02/E05 四年级 A/B/C 三级
- [ ] 按年级知识点拆分（`textbook/g4_subtraction_borrow_PEP.md` 等）— 后续扩展
- [ ] Dify Knowledge Base 导入格式对齐 — 后续扩展

## 阶段五点五：班级森林 + 多轮模拟

- [x] DB 新增 `practice_weeks`、`student_error_stats` 表（逐错因准确率跟踪）
- [x] 扩展 `StudentProfile`：`accuracy_by_error_code` + `weekly_accuracy` 字段
- [x] 新建 `forest_service.py` + `GET /api/classes/{id}/forest` 端点
- [x] 前端新增类型：`ClassForestResponse`、`StudentTree`、`WeeklyAccuracy`
- [x] 前端 Mock 数据：10 学生 × 8 周班级森林完整模拟
- [x] 作业模板升级：E01/E02/E03/E04/E05/E07/E08/E11 全部 A/B/C 三级难度
- [x] 自适应选题：根据学生薄弱错因加权选题
- [x] 多轮模拟器 `simulate_multiround.py`：8 周 × 10 学生 × 学生改进模型
- [x] 前端组件：`ClassForestGrid`、`StudentTreeCard`、`StudentDetailDrawer`、`AccuracyTrendChart`
- [x] 首页重构为班级森林全景（替换原 Hero 页面）
- [x] API 客户端新增 `getClassForest()`

## 阶段六：LLM 接入（DeepSeek API 预留）

- [ ] LLM 调用接口抽象层（`BaseLLMProvider`）
- [ ] DeepSeek provider 实现
- [ ] `LLMNode`（Pipeline 中的 LLM 节点）
- [ ] LLM 场景 1：教师摘要润色
- [ ] LLM 场景 2：学生引导语生成
- [ ] LLM 场景 3：个性化作业生成
- [ ] 所有 LLM 输出保留 `pending_teacher_review`

## 阶段七：Dify 对齐与集成

- [ ] 导出 OpenAPI spec，整理为 Dify Tool 可导入格式
- [ ] 后端新增 `conversation_id` 支持
- [ ] 设计 Dify V3 工作流
- [ ] Dify 网页端配置并测试 V3
- [ ] 验证 Dify WebApp 交互入口
- [ ] 前端补齐技术与流程页
