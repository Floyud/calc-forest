# AGENTS.md

## Project

"我的计算森林" — primary-school math calculation diagnosis Agent for the 《创AI》 competition.

Four workspaces with distinct ownership:

| Directory | Purpose | Tech |
|---|---|---|
| `development/` | FastAPI backend MVP, tests, synthetic demo data | Python (pyt0 env) |
| `docs/` | Specs, engineering docs, competition materials, source materials | Markdown |
| `calc_forest/` | Product-side work: Dify workflows, Next.js frontend | YAML / TypeScript |
| `给mom看的/` | Teacher-facing user docs (使用手册, 功能介绍, 教育理念) | Markdown |

## Commands

All Python commands **must** use the `pyt0` conda environment:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python
```

Run tests (use `-s` — pytest capture has temp-file issues in this env):

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

Run a single test:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py::test_borrow_error -q
```

Start API:

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend (in `calc_forest/web/`):

```bash
npm run dev    # dev server
npm run lint   # eslint
npm run build  # production build  (use --no-lint flag via npx)
```

**Note:** Next.js version is 15.5 — use App Router conventions (`"use client"`, `next/dynamic`). `node_modules/next/dist/docs/` does not exist in this installation; refer to nextjs.org docs instead. Build with `npx next build --no-lint` (ESLint flat config has issues).

## Architecture

**FastAPI entrypoint:** `development/app/main.py`

- `/health` — health check
- `/api/diagnose` — error diagnosis (rule-based, no LLM for arithmetic)
- `/api/practice/recommend` — practice items based on error code
- `/api/tree-species` — 8 core tree species config
- `/api/encouragements` — encouragement rules config
- `/api/dify/session-draft` — combined endpoint for Dify workflow
- `/api/dify/full-pipeline` — full pipeline (diagnosis + profile update + growth)
- `/api/students/{id}` — student entity
- `/api/students/{id}/profile` — student profile (with per-error-code accuracy + weekly accuracy)
- `PATCH /api/students/{id}/profile` — update personality tags, learning style, notes
- `/api/students/{id}/trajectory` — per-unit error trajectory
- `/api/students/{id}/growth` — student growth progress
- `GET /api/students/{id}/mastery` — BKT mastery per error code (Bayesian Knowledge Tracing)
- `POST /api/tts/generate` — Edge-TTS text-to-speech, returns MP3 audio
- `/api/classes/{id}` — class entity
- `/api/classes/{id}/summary` — class summary stats
- `/api/classes/{id}/forest` — class forest view (all students' trees + weekly accuracy)
- `/api/cycles/current` — current academic cycle
- `/api/knowledge/search` — FTS5 knowledge base search
- `/api/homework/generate` — generate homework (adaptive difficulty A/B/C)
- `/api/homework/assign` — assign homework
- `/api/homework/submit` — submit homework answers
- `/api/homework/grade` — auto-grade + diagnose + update profile
- `POST /api/homework/{id}/generate-pdf` — generate PDF (weasyprint + jinja2)
- `GET /api/homework/{id}/pdfs` — list generated PDFs
- `/api/quiz/generate` — generate in-class quiz (procedural problem generation)
- `/api/quiz/{id}` — get quiz with problems
- `/api/quiz/{id}/response` — record teacher class response (mostly_correct/mixed/mostly_wrong)
- `/api/quiz/{id}/summary` — quiz summary with error distribution
- `/api/curriculum/units` — teaching units (人教版六年级下册)
- `GET /api/curriculum/schedule/{class_id}` — weekly teaching schedule
- `PUT /api/curriculum/schedule/{class_id}` — update schedule (custom drag)
- `/api/curriculum/calendar` — academic calendar weeks
- `/api/ocr/stub` — OCR stub (returns 501)
- `POST /api/ocr/upload` — OCR upload stub (returns 501)

**Service layer:** `development/app/services/`
- `diagnosis.py` — pure rule-based diagnosis (regex + arithmetic evaluation via `ast`/`operator`)
- `practice.py` — practice recommendation by error code and guidance mode
- `growth.py` — tree species and encouragement config loaders
- `session_draft.py` — combines diagnosis + practice + guidance into one Dify-ready payload
- `student_service.py` — student CRUD + profile with per-error-code accuracy tracking
- `forest_service.py` — class forest view (batch-fetched, ~7 queries instead of N+1)
- `homework_service.py` — homework generation with adaptive difficulty (A/B/C) per error code
- `grading_service.py` — auto-grading with diagnosis pipeline + `update_error_stats()` integration
- `cycle_service.py` — academic cycle and growth queries
- `knowledge_service.py` — FTS5 full-text search over knowledge base
- `class_service.py` — class CRUD and summary
- `problem_generator.py` — procedural problem generation for E01-E11 (infinite supply, A/B/C difficulty)
- `quiz_service.py` — in-class quiz CRUD + teacher response recording + summary
- `curriculum_service.py` — teaching units, schedule, calendar, student trajectory
- `pdf_service.py` — PDF homework generation (weasyprint + jinja2)
- `profiles.py` — student/class profile summaries with weak knowledge point analysis (`get_student_profile_summary()`, `get_class_profile_summary()`)
- `summaries.py` — class-level error summaries (`get_class_error_summary()`, `get_class_period_summary()`, `get_error_code_breakdown()`)

**Pipeline layer:** `development/app/pipeline/`
- `__init__.py` — `BaseNode`, `Pipeline`, `NodeResult`, `NodeStatus`
- `diagnosis_node.py`, `practice_node.py`, `growth_config_node.py`
- `profile_update_node.py`, `growth_update_node.py`, `homework_gen_node.py`
- `session_draft_pipeline.py`, `response_assembler.py`, `student_feedback_builder.py`

**Schemas:** `development/app/schemas.py` — all Pydantic models (40+ classes). Key additions: `WeakKnowledgePoint` (error_code + unit_id + unit_title + knowledge_point + typical_error + accuracy + mastery_zone), enriched `Student` model (student_number, personality_tags, learning_style, notes).

**Database:** 21 data tables in `development/app/db.py` (`_SCHEMA_SQL`):
`students`, `classes`, `academic_cycles`, `diagnosis_history`, `student_cycle_progress`, `homework`, `homework_problems`, `homework_submissions`, `student_answers`, `practice_weeks`, `student_error_stats`, `quiz_sessions`, `quiz_problems`, `quiz_responses`, `teaching_units`, `teaching_schedule`, `calendar_weeks`, `student_error_trajectory`, `scanned_submissions`, `homework_pdfs`, `error_code_knowledge_map` (30 rows mapping E01-E11 to 人教版六年级下册 units)
Plus 6 FTS5 virtual tables for knowledge base search.

**Static data:** `development/data/` — JSON files + SQLite DB + knowledge base markdown.

**Simulators:** `development/scripts/`
- `seed_data.py` — seed 10 students, 1 class, 4 cycles, 24 demo records
- `seed_curriculum.py` — seed 人教版六年级下册 6 units, 18 weeks, 10 students, calendar
- `seed_knowledge_map.py` — seed 30-row E01-E11 → 人教版六年级下册知识点映射
- `simulate_homework.py` — single-round 10-student homework simulation
- `simulate_multiround.py` — 8-week multi-round simulation with adaptive difficulty (basic)
- `simulate_realistic.py` — **realistic 8-week simulation** with 3-tier students (优秀/中等/需关注), per-error-code accuracy modeling, streak-based improvement tracking, error-specific wrong answer generators (E01-E11), and adaptive difficulty progression. Generates 218 homework records, 506 submissions, 2111 answers

**Frontend pages:** `calc_forest/web/src/app/`
- `/` — Home (班级森林 grid with emotional states, zoom toggle)
- `/classroom` — 课堂模式 (prep view → whiteboard → summary)
- `/diagnose` — 诊断演示
- `/forest` — 森林成长

**Frontend components:** `calc_forest/web/src/components/`
- `classroom/ClassPrepView.tsx` — class error analysis + quiz configuration
- `classroom/WhiteboardDisplay.tsx` — full-screen forest-themed whiteboard with animated problem display
- `classroom/QuizSummaryView.tsx` — post-quiz summary with error distribution
- `forest/` — SVG tree system, forest background, student cards, 3-tab detail drawer (overview/trajectory/profile)
- `forest/ErrorRadarChart.tsx` — E01-E11 radar chart in StudentDetailDrawer
- `forest/ClassErrorHeatmap.tsx` — student×error_code matrix heatmap on home page
- `layout/` — navbar (4 tabs), footer
- `ui/` — shadcn/ui base-nova primitives
- `GuidanceChat` — Edge-TTS backend integration with Web Speech API fallback

**Frontend performance:** Heavy components use `next/dynamic` (WhiteboardDisplay, AccuracyTrendChart, StudentDetailDrawer). `recharts` only loads on drawer open. `optimizePackageImports` enabled in `next.config.ts`. Botanical page uses lazy loading + collapsible facts for 60% DOM reduction.

## Critical Constraints

1. **No LLM for arithmetic correctness.** Diagnosis is rule-based only. LLM may summarize or explain but never decide if an answer is correct.
2. **Teacher review gate.** All AI output carries `review_status: "pending_teacher_review"`. Never bypass.
3. **Synthetic data only.** No real student data. Use `development/data/demo_answer_records.json`.
4. **Error codes `E01`-`E11`, `E99`.** Source of truth is `docs/specs/04_error_taxonomy.md`.
5. **Guidance walks the child through thinking, never dumps the answer.**
6. **No rankings, forced streaks, holiday pressure, or parent pressure.**
7. **MVP is teacher-side only.** Full student app, parent app, OCR, complete textbook graph are future scope unless explicitly requested.

### Exercise Types (题库范围)

"计算" 不局限于四则运算，涵盖所有需要计算能力的题型：

| 类型 | 说明 | 示例 |
|---|---|---|
| 口算 | 心算快速题 | 25×4=, 3.6÷0.9= |
| 竖式计算 | 列竖式的多位数运算 | 3.14×2.5, 402-178 |
| 脱式计算 | 递等式/分步计算 | 3.6×2.5+4.8÷1.2 |
| 简便运算 | 运算律/巧算 | 125×32, 99×37+37 |
| 列式计算 | 文字题转算式 | "25的4倍与36的差是多少" |
| 图形计算 | 面积/周长计算 | 圆面积、组合图形面积 |
| 分数运算 | 分数四则混合 | 2/3+5/6×3/5 |

### Teaching Principles (教学理念)

1. **分层递进**: 习题有层次，根据答题情况逐步提高难度（A基础→B中档→C高档）
2. **靶向强化**: 根据学生实际学习能力和薄弱点出题，薄弱点强化训练，举一反三
3. **算理引导**: 不会做或做错时，一步步引导思考，让学生真正理解算理、学会算法
4. **语音交互**: Edge-TTS 已集成（后端 `/api/tts/generate`），前端 GuidanceChat 带 Web Speech API 回退；长期目标 — 像小老师一样辅导孩子一步步做题
5. **情绪价值**: 引导过程中用严谨的数学语言，同时给予充足情绪支持 — 不断肯定孩子，也明确指出问题所在

## Key Context Files

- `Agent.md` — session handoff, project rules, and status (update when scope/paths/APIs change)
- `docs/project_management/task_board.md` — current task status (updated with BI-018 through BI-026)
- `docs/project_management/decision_log.md` — major decisions (product leap decision recorded)
- `docs/specs/04_error_taxonomy.md` — error code definitions (PM-facing source of truth, includes 人教版六年级下册 knowledge mapping)
- `docs/competition/demo_script_v2.md` — 5-act frontend-first demo narrative
- `docs/competition/elevator_pitch.md` — 30-second competition pitch

## Dify Cloud Integration

**3 Dify Apps — ⚠️ 全部返回 401，需要从 DSL 重新导入:**

| App | Type | API Key | 状态 |
|---|---|---|---|
| 学生引导助手 | chatflow | `app-6Kq0zwnO8MIZcQZoMbDoPc0c` | 401 — 需重建 |
| 教师诊断助手 | workflow | `app-Sf6Hx45Iv9Zjm3ORUUlFmIrj` | 401 — 需重建 |
| AI批改画像助手 | workflow | `app-kxypiB5ho1osryrXPpEgSq6j` | 401 — 需重建 |

**修复方法:** 删除旧 app → 从 `calc_forest/dify/` 导入修正后的 DSL → 绑定知识库 → 发布

**知识库:** `我的计算森林知识库`
- Dataset ID: `e65030a0-3076-4cd1-b646-d834ecafa55e`
- KB API Key: `dataset-JAnfqaoKgN4nI6ccnFUj9sF2`
- Embedding: `OpenAI/text-embedding-3-large`
- 10 个中文命名的 Markdown 文档，7 个领域分类
- 文件源: `knowledge_base/` 目录（本地 = source of truth）
- 同步脚本: `knowledge_base/sync_to_dify.py`

**DSL 文件:** `calc_forest/dify/`
- `dsl_student_guidance_chatflow.yml` — 学生引导
- `dsl_teacher_diagnosis_workflow.yml` — 教师诊断
- `dsl_ai_grading_profile_workflow.yml` — AI批改画像

**Dify 输入变量映射:**
- 学生引导 (chatflow): 无自定义输入，`query` = 学生问题
- 教师诊断 (workflow): `diagnosis`(必填), `student_info`(必填), `session_history`(选填)
- AI批改 (workflow): `mode`(必填: grading/profiling), `grading_results`, `student_info`, `error_stats`, `accuracy_trend`

**已知问题 (已在 DSL 中修复):**
- ~~3 个应用的「知识检索」节点 retrieval_mode~~ → 已全部改为 `single`
- ~~provider 字段需要 `langgenius/deepseek/deepseek` 完整格式~~ → 已修复
- ~~knowledge-retrieval 使用 `query` 字段~~ → 已改为 `query_variable_selector`
- DSL 文件是 source of truth，Cloud Dify 需从 DSL 重新导入

## Local Dify Deployment

**地址:** `http://127.0.0.1:18080`
**Dify 版本:** 1.14.0
**部署目录:** `/home/lyzhang/dify/docker/`

**管理员:** `lzha0301@student.monash.edu` / `zly123456`
**Console API 登录:** password 须 base64 编码

**已安装插件:**
- `langgenius/openai:0.3.8`
- `langgenius/deepseek:0.0.15`

**已配置模型供应商:**
- DeepSeek LLM (deepseek-chat) — credentials configured ✅
- OpenAI Embedding — ⚠️ 连接验证失败（OpenAI 插件发送 tiktoken 编码的 token ID，本地服务无法解码）
- 等待 bge-m3 下载完成后，考虑使用其他插件（ollama/localai）替代

**本地模型服务:** `scripts/local_model_server.py`
- tmux session `models`, `--host 0.0.0.0 --port 8090`
- Embedding: `BAAI/bge-m3` (1024d) ✅
- Reranker: `jinaai/jina-reranker-v3`
- GPU: CUDA (RTX 5070 Ti 12GB)
- Docker 访问地址: `http://172.20.0.1:8090`
- 支持 `encoding_format=base64` 和 `/v1/models` 端点

**双线路由架构 (dify_client.py):**
- `Local Dify → Cloud Dify → DeepSeek 直连` 三级回退
- 环境变量: `LOCAL_DIFY_ENABLED`, `LOCAL_DIFY_BASE_URL`, `LOCAL_DIFY_WORKFLOW_*_KEY`

**本地 Dify Apps (已导入、已发布、已验证):**

| App | Type | API Key | App ID |
|---|---|---|---|
| 学生引导助手 | advanced-chat | `app-WhZiyxSsRzCySLHIc5aeB35E` | `80c2a91f-781d-4321-bc8a-36b9bfff060d` |
| 教师诊断助手 | workflow | `app-RA3FRdUFJUgyykmf3wZ99kbX` | `45757ec4-4517-4c75-9e42-a48b1540da52` |
| AI批改画像助手 | workflow | `app-hVqrf2hyY4Qx1dcYx21XRxpW` | `6464ffec-c67a-4af5-ae3d-a318a798143d` |

**本地知识库:** `我的计算森林知识库`
- Dataset ID: `8a588b72-2c02-4d34-b9ef-4f53dee606b0`
- Indexing: economy (关键词索引，待配置 embedding 后切换为 high_quality)
- 10 个中文命名的 Markdown 文档已上传

**关键端口:**
| 服务 | 端口 |
|---|---|
| Local Dify | 18080 |
| 本地模型服务 | 8090 |
| FastAPI 后端 | 8000 |
| Next.js 前端 | 3002 |

## Known Gaps

- Mixed-operation parenthesis diagnosis and two-digit multiplication partial-product alignment cases not yet covered (BI-011, BI-012).
- ~~`profiles.py` and `summaries.py` are stubs~~ → BI-006/BI-008 已实现。
- Growth milestone update logic not implemented (BI-015).
- 4-step guided feedback (standard mode) not yet in code (BI-016).
- Grade 1-2 mental arithmetic diagnosis rules not yet implemented (BI-017).
- Dify 知识检索 retrieval_mode 已修复（全部改为 `single`，`query` → `query_variable_selector`）。
- Cloud Dify 所有 3 个 API 返回 401（需删除旧 app → 从 DSL 重新导入）。
- Local Dify Embedding 供应商连接验证失败（OpenAI 插件与本地服务不兼容）。
- ~~Frontend pages use mock data; only `/diagnose` calls real backend API~~ → **All pages connected to real backend API.** Only `/guidance` page is purely static content. `/botanical` uses API + local enrichment data.
- `problem_generation` 无独立 Dify workflow，始终走 DeepSeek 回退。
- `.mcp.json` 配置了 Playwright MCP（需重载 session 生效，设置 `TMPDIR=/tmp` 解决 WSL Unix socket 问题）。

## CI/CD and Infrastructure

**GitHub Actions:** CI pipeline with DB seeding, test exclusion for E2E.

**Docker Compose:** backend + frontend + dify profile.

**Test counts:**
| Layer | Count |
|---|---|
| Backend (pytest) | 105 |
| Frontend (Vitest) | 73 |
| Playwright E2E | 6 |
| Dify E2E | 3 |

## Product Strategy

**核心定位:** "从功能实现者升级为产品主导者"

- **可视化优先:** 让 E01-E11 被雷达图看见、被 TTS 听见、被粒子动画感受到
- **教师审核 = 合规优势:** 2025 教育部 13 岁以下禁独立 AI，教师审核门是我们的合规护城河
- **森林隐喻 = 情感差异化:** 对标 Duolingo 猫头鹰，用成长隐喻替代排名压力

**竞赛演示叙事 (5幕):**
1. 班级森林总览 — 看见每棵树的情绪状态
2. 点击学生 — 雷达图 + 薄弱知识点卡片 + 掌握度徽章
3. 课堂模式 — 白板展示 → 即时反馈 → 错误分布
4. 引导对话 — Edge-TTS 语音 + 步步引导（不给答案）
5. 成长轨迹 — 时间线 + 作业自适应难度

## Competition Materials

- `docs/competition/demo_script_v2.md` — 5-act frontend-first demo narrative
- `docs/competition/elevator_pitch.md` — 30-second competition pitch
- `docs/project_management/decision_log.md` — product leap decision recorded
- `docs/project_management/task_board.md` — updated with BI-018 through BI-026
- `docs/specs/04_error_taxonomy.md` — added 人教版六年级下册 knowledge mapping section
