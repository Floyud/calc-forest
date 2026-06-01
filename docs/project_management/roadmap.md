# 我的计算森林 — 功能演进路线图

> 最后更新：2026-05-19
>
> 维护方式：`[x]` 已完成，`[ ]` 未完成。每完成一项即时更新。
>
> 相关文档：`docs/project_management/task_board.md` · `docs/engineering/architecture.md`

---

## 阶段一：数据基础层（SQLite + 实体模型）✅

- [x] 引入 `aiosqlite` 依赖，建立数据库连接管理（`db.py`）
- [x] 设计并创建表结构：students, classes, academic_cycles, diagnosis_history, student_cycle_progress
- [x] 新增 Pydantic 模型：Student, StudentProfile, Class, AcademicCycle, StudentCycleProgress
- [x] 建种子数据脚本
- [x] 实现 Student CRUD service + API 端点
- [x] 实现 Class CRUD service + API 端点
- [x] 实现 AcademicCycle 查询 service + API 端点
- [x] 迁移现有 demo_answer_records.json 到 SQLite

## 阶段二：后端编排模式重构（Pipeline）✅

- [x] 设计 Pipeline Node 接口（BaseNode）
- [x] 实现轻量 Pipeline 编排器
- [x] 将 diagnosis.py 重构为 DiagnosisNode
- [x] 将 practice.py 重构为 PracticeNode
- [x] 新增 GrowthConfigNode, ProfileUpdateNode, GrowthUpdateNode
- [x] 将 session_draft.py 改为 Pipeline 组装模式
- [x] 提取 response_assembler.py, student_feedback_builder.py
- [x] 新增 POST /api/dify/full-pipeline 端点

## 阶段三：作业生命周期 ✅

- [x] 设计 homework, homework_problems, homework_submissions, student_answers 表
- [x] 实现 HomeworkGenNode
- [x] POST /api/homework/generate — 生成作业
- [x] POST /api/homework/assign — 分发作业
- [x] POST /api/homework/submit — 学生提交答案
- [x] POST /api/homework/grade — 自动批阅 + 诊断 + 更新画像
- [x] 作业模拟器
- [x] GET /api/students/{id}/profile 完整版

## 阶段四：校历与成长系统 ✅

- [x] 创建标准中国公立小学校历配置
- [x] GET /api/cycles/current 查询当前周期
- [x] GET /api/students/{id}/growth 查看成长进度
- [x] POST /api/growth/record-practice 记录练习 + 推进里程碑
- [x] 9 阶段里程碑自动计算
- [x] 鼓励语匹配逻辑完善

## 阶段五：轻量知识库 ✅

- [x] 按错因码拆分知识库文件
- [x] SQLite FTS5 全文索引
- [x] GET /api/knowledge/search?q=... 后端查询端点
- [x] 补全错因文档：E01-E11 全部覆盖
- [x] 补全作业模板：全部 A/B/C 三级难度
- [x] 知识库重构为 135+ 文件（44 错因类型 + 1~6 年级 + 题库）
- [x] Dify 知识库同步脚本 (sync_to_dify.py)

## 阶段五点五：班级森林 + 多轮模拟 ✅

- [x] DB 新增 practice_weeks, student_error_stats 表
- [x] 扩展 StudentProfile：accuracy_by_error_code + weekly_accuracy
- [x] 新建 forest_service.py + GET /api/classes/{id}/forest
- [x] 前端组件：ClassForestGrid, StudentTreeCard, StudentDetailDrawer, AccuracyTrendChart
- [x] 首页重构为班级森林全景
- [x] 作业模板升级：全部错因 A/B/C 三级
- [x] 自适应选题：根据学生薄弱错因加权选题
- [x] 多轮模拟器 simulate_multiround.py

## 阶段六：LLM 接入 ✅

- [x] LLM 客户端 (`llm_client.py`)：DeepSeek/GLM 三级回退
- [x] Dify 客户端 (`dify_client.py`)：双线路由 + 熔断器
- [x] 教师摘要润色 (generate_teacher_summary)
- [x] 学生引导语生成 (generate_student_feedback)
- [x] 个性化作业生成 (ai_generate_problems)
- [x] 所有 LLM 输出保留 pending_teacher_review
- [x] 批改评语生成 (ai_grade_answers)
- [x] AI 画像分析 (ai_analyze_profile)

## 阶段七：Dify 对齐与集成 ✅

- [x] 本地 Dify 部署 (127.0.0.1:18080)
- [x] 3 个 Dify App 导入（教师诊断、学生引导、AI批改画像）
- [x] Dify 知识库配置（5 个压缩文档）
- [x] DSL 文件管理 (`calc_forest/dify/`)
- [x] Dify V2 工作流设计
- [ ] Cloud Dify 修复（3 个 App 全部 401）

## 阶段八：前端完整实现 ✅

- [x] Next.js 15.5 App Router 搭建
- [x] 教师端 10 个页面（登录 + 9 个功能页）
- [x] 学生端 7 个页面（登录 + 6 个功能页）
- [x] 44 个组件（森林可视化、ECharts 图表、课堂视图、作业表单等）
- [x] 集中式 API 客户端 + TanStack Query hooks
- [x] TypeScript 类型定义（504 行）
- [x] shadcn/ui + Tailwind CSS 4 + Framer Motion

## 阶段九：作业增强 ✅

- [x] 作业 PDF 生成 (xelatex + weasyprint)
- [x] 批量流水线 (batch-pipeline)
- [x] 作业生命周期管理 (homework_lifecycle)
- [x] 作业分析 (homework_analytics)
- [x] 班级作业分析
- [x] 学生作业汇总

## 阶段十：课堂与测验 ✅

- [x] 课堂测验生成/响应/统计
- [x] 实时统计 (live-stats)
- [x] 学生答题 (student-answer)
- [x] 课表管理 (timetable)
- [x] 自动布置作业 (auto-assign)

## 阶段十一：认证与安全 ✅

- [x] 教师认证 (auth.py)
- [x] 学生认证 (student_auth.py)
- [x] 密码哈希 (bcrypt)

## 阶段十二：OCR 与多模态 🔄

- [x] PaddleOCR 本地识别 (ocr_service.py)
- [x] 百度智能纠错 API (baidu_ocr_service.py)
- [x] OCR 路由器 (ocr.py)
- [ ] 完整扫码批改流程（端点返回 501）

## 阶段十三：报告系统 ✅

- [x] 学生报告 PDF 生成
- [x] 班级报告 PDF 生成
- [x] 报告列表查询

## 阶段十四：掌握度与分析 ✅

- [x] BKT 掌握度计算 (mastery_service.py)
- [x] 学生 AI 分析
- [x] 班级 AI 画像
- [x] 错因轨迹分析
- [x] 学生仪表盘

## 待办

- [ ] 混合运算括号诊断 (BI-011)
- [ ] 两位数乘法部分积对齐 (BI-012)
- [ ] 成长里程碑更新逻辑 (BI-015)
- [ ] 4 步标准引导反馈 (BI-016)
- [ ] 一二年级口算诊断规则 (BI-017)
- [ ] Cloud Dify 修复
- [ ] 完整扫码批改流程
