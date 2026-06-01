# AGENTS.md

## 项目

**我的计算森林** — 小学数学计算错因诊断 Agent，参加《创AI》竞赛。

**核心定位：AI批阅，教师把关。** AI自动批改作业并诊断错因，教师审核确认后生效。这是2025教育部13岁以下禁独立AI政策的合规护城河。

| 目录 | 用途 | 技术栈 |
|---|---|---|
| `calc_forest/` | 产品工作区：后端 + 前端 + Dify 工作流 | Python / TypeScript / YAML |
| `calc_forest/backend/` | FastAPI 后端、测试、脚本、数据 | Python (pyt0 env) |
| `calc_forest/web/` | Next.js 前端（教师端 + 学生端） | TypeScript |
| `calc_forest/dify/` | Dify 工作流 DSL + 知识库源文件 | YAML / Markdown |
| `knowledge_base/` | Dify 知识库源文件（本地=source of truth） | 中文 Markdown |
| `docs/` | 产品文档、工程文档、竞赛材料 | Markdown |
| `给mom看的/` | 教师端用户文档（使用手册、功能介绍） | HTML |

---

## 命令

### 后端 (Python — 必须用 pyt0 环境)

```bash
# 运行全部测试
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/ -q --ignore=tests/test_e2e_smoke.py --ignore=tests/test_dify_e2e.py -k "not full_pipeline"

# 启动 API
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端 (Next.js 15.5 — App Router)

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/web
npm run dev                              # 开发服务器 (port 3000)
npx next build --no-lint                 # 生产构建 (ESLint flat config 有问题，必须 --no-lint)
npx tsc --noEmit                         # 类型检查
```

### 模拟数据

```bash
# 真实感8周模拟（3档学生、自适应难度、E01-E11错因模拟器）
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_realistic.py
```

---

## 架构

> 详细架构文档见 `docs/engineering/architecture.md`

### 后端 API（13 个路由器，~75 个端点）

| 路由器 | 前缀 | 端点数 | 功能 |
|---|---|---|---|
| `diagnosis.py` | `/api` | 6 | 错因诊断、Dify 聊天代理、练习推荐、会话草稿、全流程管道、SSE 流式管道 |
| `homework.py` | `/api/homework` | 16 | 作业生成/布置/提交/AI批改/PDF/分析/生命周期/批量流水线 |
| `student.py` | `/api/students` | 10 | 学生实体/画像/轨迹/成长/掌握度/AI分析/引导上下文 |
| `student_api.py` | `/api/students` | 10 | 学生端：仪表盘/待做作业/练习会话/作业PDF |
| `quiz.py` | `/api/quiz` | 6 | 课堂测验生成/响应/统计/实时状态 |
| `config.py` | `/api` | 12 | 健康检查/树种/鼓励语/LLM状态/TTS/PDF/报告生成 |
| `curriculum.py` | `/api` | 6 | 教学单元/课表/日历/周次计算 |
| `classroom.py` | `/api/classes` | 5 | 班级详情/摘要/森林视图/HDF/AI画像 |
| `knowledge.py` | `/api` | 6 | 知识库搜索/知识点/知识图谱/题库/题型 |
| `auth.py` | `/api/auth` | 2 | 教师登录/当前教师信息 |
| `student_auth.py` | `/api/student-auth` | 3 | 学生登录/身份验证/班级学生列表 |
| `ocr.py` | `/api/ocr` | 4 | OCR 识别/作业识别/图片上传/**百度智能作业批改** |
| `timetable.py` | `/api/timetable` | 6 | 课表查询/更新/周视图/今日/自动布置/手动布置 |

### 服务层 (`calc_forest/backend/app/services/`)

| 服务 | 职责 |
|---|---|
| `diagnosis.py` | 纯规则诊断引擎 (regex + ast/operator)，34KB 核心逻辑 |
| `problem_generator.py` | 程序化出题 E01-E11（142KB，A/B/C 难度，无限供应） |
| `grading_service.py` | **AI自动批改** + 诊断流水线 + 错误统计更新 |
| `homework_service.py` | 作业生成（自适应难度 A/B/C） |
| `homework_analytics.py` | 作业分析（批量查询，无 N+1） |
| `homework_lifecycle.py` | 作业生命周期管理（全流程 + 单步） |
| `pdf_service.py` | PDF 生成（xelatex + weasyprint，47KB） |
| `quiz_service.py` | 课堂测验生成/响应/统计 |
| `student_simulator.py` | 真实感学生答题模拟器（演示用） |
| `llm_client.py` | DeepSeek/GLM 三级回退（官方→代理→智谱） |
| `dify_client.py` | Dify 双线路由（本地→云端→直连）+ 熔断器 |
| `knowledge_rag_service.py` | RAG 知识检索（知识点+例题+进度） |
| `knowledge_service.py` | 知识库搜索/知识点列表/题型管理 |
| `forest_service.py` | 班级森林视图 + 情绪状态计算 |
| `curriculum_service.py` | 人教版六年级课程体系 + 学生轨迹 |
| `profiles.py` | 学生/班级画像摘要 + 薄弱知识点分析 |
| `summaries.py` | 班级错因汇总/周期汇总/错因分解 |
| `student_service.py` | 学生 CRUD/错因统计/薄弱点/掌握度/引导上下文 |
| `student_dashboard_service.py` | 学生端仪表盘数据 |
| `student_practice_service.py` | 学生自主练习会话管理 |
| `student_auth_service.py` | 学生认证 + 会话管理 |
| `auth_service.py` | 教师认证 + 权限 |
| `mastery_service.py` | BKT（贝叶斯知识追踪）掌握度计算 |
| `growth.py` | 树种列表/鼓励语规则 |
| `growth_milestone.py` | 成长阶段计算/练习天数记录/里程碑 |
| `cycle_service.py` | 学习周期管理/成长数据 |
| `class_service.py` | 班级查询/摘要 |
| `practice.py` | 练习推荐 |
| `session_draft.py` | Dify 会话草稿构建 |
| `ocr_service.py` | 本地 OCR 引擎（PaddleOCR） |
| `baidu_ocr_service.py` | **百度智能作业批改** API（异步两步调用：create_task → get_result，OAuth2 认证，461 行） |
| `tts_service.py` | Edge-TTS 语音合成 |
| `upload_service.py` | 文件上传管理 |
| `archetype.py` | 学生原型分类 |
| `timetable_service.py` | 课表管理/自动布置作业 |
| `utils.py` | 密码哈希/JSON 列/通用工具 |

### 处理管道 (`calc_forest/backend/app/pipeline/`)

| 模块 | 职责 |
|---|---|
| `grading_pipeline.py` | 批改管道编排（10KB） |
| `diagnosis_node.py` | 诊断节点 |
| `profile_update_node.py` | 画像更新节点 |
| `growth_update_node.py` | 成长更新节点 |
| `growth_config_node.py` | 成长配置节点 |
| `practice_node.py` | 练习推荐节点 |
| `homework_gen_node.py` | 作业生成节点 |
| `teacher_summary_node.py` | 教师摘要节点 |
| `student_feedback_builder.py` | 学生反馈构建 |
| `response_assembler.py` | 响应组装 |
| `session_draft_pipeline.py` | 会话草稿管道 |

### 数据访问层 (`calc_forest/backend/app/repositories/`)

| 模块 | 职责 |
|---|---|
| `diagnosis_repo.py` | 诊断历史查询 |
| `homework_repo.py` | 作业/提交/答案批量查询 |
| `stats_repo.py` | 错因统计查询 |

### 数据库 (`calc_forest/backend/app/db.py`)

33 张数据表 + 1 个 FTS5 虚拟表。

**基础实体：**
- `students`, `classes`, `teachers`, `academic_cycles`

**作业闭环：**
- `homework`, `homework_problems`, `homework_submissions`, `student_answers`
- `homework_pdfs`, `scanned_submissions`, `grading_comments`

**诊断与错因：**
- `diagnosis_history`, `student_error_stats`, `student_error_trajectory`
- `error_code_knowledge_map` — 错因代码 → 人教版知识点映射

**课堂测验：**
- `quiz_sessions`, `quiz_problems`, `quiz_responses`, `quiz_student_answers`

**学生成长：**
- `student_cycle_progress`, `practice_weeks`
- `student_practice_sessions`, `student_practice_problems`

**教学体系：**
- `teaching_units`, `teaching_schedule`, `calendar_weeks`
- `timetable`（课表，运行时创建）

**知识库：**
- `knowledge_points`, `concept_relations`, `problem_bank`
- `knowledge_points_fts` — FTS5 全文搜索虚拟表
- `week_calc_mapping` — 周次 → 错因代码映射

**画像与报告：**
- `profile_snapshots`
- `exercise_types` — 题型定义

### 前端 (`calc_forest/web/src/`)

Next.js 15.5 App Router，教师端 + 学生端双布局。

**教师端 (`(teacher)/`)：**

| 页面 | 路由 | 功能 |
|---|---|---|
| 登录 | `/login` | 教师登录 |
| 首页 | `/` | 班级森林网格 + 错因热力图 + 情绪状态 |
| 课堂模式 | `/classroom` | 备课→白板→测验→总结 |
| 作业闭环 | `/homework` | 生成→布置→作答→**AI批阅**→教师审核 |
| 课表 | `/schedule` | 教学进度 + 自动布置作业 |
| 诊断演示 | `/diagnose` | 单题诊断演示 |
| 引导对话 | `/guidance` | Edge-TTS 语音引导（不给答案） |
| 森林成长 | `/forest` | 学生成长详情 |
| 植物百科 | `/botanical` | 树种知识卡片 |
| AI 对话 | `/chat` | Dify 聊天代理 |

**学生端 (`(student)/`)：**

| 页面 | 路由 | 功能 |
|---|---|---|
| 登录 | `/s/login` | 学生登录 |
| 首页 | `/s/home` | 学生仪表盘 |
| 成长 | `/s/growth` | 个人成长树 |
| 练习 | `/s/practice` | 自主练习 |
| 扫码批改 | `/s/scan/:hwId` | OCR 拍照批改 |
| 作业详情 | `/s/homework/:id` | 查看作业 + 提交 |
| 测验 | `/s/quiz/:id` | 课堂测验 |

**核心组件（44 个）：** 森林可视化（含 Canvas 渲染器 + 粒子系统）、ECharts 图表（雷达/趋势/热力图）、课堂视图、作业表单、引导对话、诊断管道进度等。

**API 层：** 集中式 fetch 封装（重试 + 45s 超时），TanStack Query hooks，完整 TypeScript 类型定义（504 行）。

**图表:** ECharts 6.x（雷达图、趋势线、热力图、柱状图）。无 recharts。

---

## 硬约束

1. **算术对错只用规则引擎。** LLM 可以总结或解释，但绝不能判断答案对错。
2. **教师审核门。** 所有 AI 输出带 `review_status: "pending_teacher_review"`，绝不能绕过。
3. **合成数据。** 不使用真实学生数据。
4. **错因代码体系。** 知识类 E-K01~E-K23 + 习惯类 E-H01~E-H21。唯一来源：`docs/specs/04_error_taxonomy.md` + `knowledge_base/01_error_taxonomy/`。
5. **引导不倒答案。** 步骤引导思考过程，永远不直接给出答案。
6. **无排名、无打卡、无家长压力。**
7. **教师端 MVP + 学生端基础功能。** 教师端为核心，学生端含仪表盘/练习/扫码/作业查看/测验。家长端、完整 OCR 为未来范围。

---

## 文档索引

> 详细导航见 `docs/README.md`

### 📋 产品规格 (`docs/specs/`)

| 文件 | 内容 |
|---|---|
| `00_project_brief.md` | 项目简介 |
| `01_prd.md` | 产品需求文档 |
| `02_mvp_scope.md` | MVP范围定义 |
| `03_user_flows.md` | 用户流程 |
| `04_error_taxonomy.md` | ⭐ 错因分类体系（E-K/E-H 定义 + 人教版知识点映射） |
| `05_data_contract.md` | 数据契约 |
| `06_acceptance_criteria.md` | 验收标准 |
| `07_risks_and_open_questions.md` | 风险与待定问题 |
| `08_forest_growth_system.md` | 森林成长体系设计 |
| `09_guidance_system.md` | 引导系统设计 |
| `10_multimodal_input.md` | 多模态输入规划（未来） |
| `teacher_feedback_digest.md` | 教师反馈摘要 |

### 🛠 工程文档 (`docs/engineering/`)

| 文件 | 内容 |
|---|---|
| `architecture.md` | ⭐ 系统架构总览（含完整端点清单、数据流、部署） |
| `api_plan.md` | API 设计方案（全部 ~75 个端点） |
| `data_model.md` | 数据模型设计（33 张表 + Pydantic 模型） |
| `dify_workflow_plan.md` | Dify 工作流方案 |
| `prompt_registry.md` | Prompt 注册表 |
| `frontend_experience_plan.md` | 前端界面规划 |
| `evaluation_plan.md` | 评测方案 |

### 🎯 竞赛材料 (`docs/competition/`)

| 文件 | 内容 |
|---|---|
| `elevator_pitch.md` | 30秒电梯演讲 |
| `demo_video_script_v2.md` | ⭐ 5幕演示脚本（最新版） |
| `evidence_checklist.md` | 证据清单 |
| `创AI_申报总纲.md` | 竞赛申报总纲 |
| `创AI_案例信息表_素材.md` | 案例信息表素材 |
| `创AI_开发与应用报告_草稿.md` | 开发报告草稿 |

### 📊 项目管理 (`docs/project_management/`)

| 文件 | 内容 |
|---|---|
| `task_board.md` | ⭐ 任务看板（当前状态） |
| `decision_log.md` | 重大决策记录 |
| `roadmap.md` | 产品路线图 |
| `session_protocol.md` | Session协议 |

### 🔬 调研材料 (`docs/research/`)

| 文件 | 内容 |
|---|---|
| `pain_points_primary_math.md` | 小学数学痛点分析 |
| `policy_and_compliance.md` | 政策合规研究 |
| `competition_tracks.md` | 竞赛赛道分析 |
| `tech_landscape.md` | 技术选型调研 |
| `coze_dify_agent_platforms.md` | Coze/Dify平台对比 |
| `teaching_schedule_and_problem_design.md` | 教学进度与出题设计 |
| `teacher_feedback_curated/` | 教师反馈整理（按来源分） |

### 📚 知识库 (`knowledge_base/`)

135+ 个中文 Markdown 文件，按领域组织：
- `00_shared/` — 错因代码定义
- `01_error_taxonomy/` — 44 个错因类型（knowledge 23 + habitual 21）
- `02_grade_content/` — 1~6 年级知识点（~50 文件）
- `03_teaching_strategies/` — 引导策略
- `04_grading_system/` — 批改系统
- `05_curriculum/` — 课程设计
- `05_growth_system/` — 成长体系
- `06_classroom/` — 课堂方法
- `07_question_bank/` — 题库（六年级上册 5 单元 × 3 难度）

通过 `sync_to_dify.py` 同步到 Dify 知识库。本地是 source of truth。

### 📖 教师文档 (`给mom看的/`)

| 文件 | 内容 |
|---|---|
| `小介绍.html` | 教师端产品介绍页面 |

---

## Dify 集成

### 本地 Dify (主要使用)

- 地址: `http://127.0.0.1:18080`
- 三级回退: `Local Dify → Cloud Dify → DeepSeek 直连`
- 3 个 App（教师诊断、学生引导、AI批改画像）
- DSL 文件: `calc_forest/dify/` (source of truth)
- 知识库: 5 个中文 Markdown 文档（压缩版）

### Cloud Dify (需修复)

3 个 App 全部 401。修复：删除旧 app → 从 `calc_forest/dify/` 导入 DSL → 绑定知识库 → 发布。

### 本地模型服务

- tmux session `models`, port 8090
- Embedding: BAAI/bge-m3 (1024d)
- Reranker: jinaai/jina-reranker-v3
- GPU: RTX 5070 Ti 12GB

---

## 端口

| 服务 | 端口 |
|---|---|
| FastAPI 后端 | 8000 |
| Next.js 前端 | 3000 |
| 本地 Dify | 18080 |
| 本地模型服务 | 8090 |

---

## 测试

| 层级 | 数量 |
|---|---|
| 后端 (pytest) | 341 passed / 9 pre-existing failures |
| 前端 (Vitest) | 73 |
| E2E (Playwright) | 6 |
| Dify E2E | 3 |

---

## Known Gaps

- 混合运算括号诊断和两位数乘法部分积对齐未覆盖 (BI-011, BI-012)
- 成长里程碑更新逻辑未实现 (BI-015)
- 4步标准引导反馈未完成 (BI-016)
- 一二年级口算诊断规则未实现 (BI-017)
- Cloud Dify 3个API返回401（需从DSL重新导入）
- Local Dify Embedding供应商连接验证失败（OpenAI插件与本地服务不兼容）
- OCR 扫码批改端点已接入百度智能作业批改 API（Baidu 优先 + 本地 OCR 回退，需配置 BAIDU_OCR_API_KEY / BAIDU_OCR_SECRET_KEY）
