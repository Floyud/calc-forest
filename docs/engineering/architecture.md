# 系统架构

> 最后更新：2026-05-28 | 基于代码库实际状态

## 总体原则

系统采用 **FastAPI 核心服务 + Dify AI 编排 + Next.js 双端前端** 架构。FastAPI 负责所有核心业务逻辑（规则诊断、数据管理、作业生命周期），Dify 负责 LLM 交互层（对话引导、批改评语、画像分析），Next.js 提供教师端和学生端 Web 界面。

```text
┌─────────────────────────────────────────────────────────┐
│                    前端层 (Next.js 15.5)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  教师端       │  │  学生端       │  │  共享组件     │   │
│  │  (teacher)/   │  │  (student)/   │  │  森林/ECharts │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘   │
│         │                 │                              │
│         └────────┬────────┘                              │
│                  │ TanStack Query + 集中式 API 客户端     │
└──────────────────┼──────────────────────────────────────┘
                   │ HTTP/REST + SSE
┌──────────────────┼──────────────────────────────────────┐
│                  │        后端层 (FastAPI)                │
│  ┌───────────────┴────────────────────────────────┐     │
│  │              13 个路由器 (~75 端点)              │     │
│  │  diagnosis│homework│student│quiz│config│...     │     │
│  └───────────────┬────────────────────────────────┘     │
│                  │                                       │
│  ┌───────────────┴────────────────────────────────┐     │
│  │              服务层 (39 个服务模块)               │     │
│  │  diagnosis│problem_generator│grading│homework   │     │
│  │  student│quiz│pdf│ocr│llm_client│dify_client   │     │
│  └───────────────┬────────────────────────────────┘     │
│                  │                                       │
│  ┌───────────────┴──────┐  ┌─────────────────────┐     │
│  │  处理管道 (pipeline/) │  │  数据访问 (repos/)   │     │
│  │  11 个节点模块        │  │  3 个仓库模块        │     │
│  └───────────────┬──────┘  └──────────┬──────────┘     │
│                  │                     │                 │
└──────────────────┼─────────────────────┼────────────────┘
                   │                     │
┌──────────────────┼─────────────────────┼────────────────┐
│                  │     数据层           │                 │
│  ┌───────────────┴──────┐  ┌──────────┴──────────┐     │
│  │  SQLite (33 张表)     │  │  文件存储            │     │
│  │  + FTS5 全文搜索      │  │  PDF/图片/上传       │     │
│  └──────────────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                   │
┌──────────────────┼──────────────────────────────────────┐
│                  │        AI 编排层                       │
│  ┌───────────────┴────────────────────────────────┐     │
│  │  Dify 工作流 (3 个 App)                         │     │
│  │  教师诊断 │ 学生引导 │ AI批改画像                 │     │
│  │  + 知识库 (5 个压缩文档)                         │     │
│  └───────────────┬────────────────────────────────┘     │
│                  │                                       │
│  ┌───────────────┴────────────────────────────────┐     │
│  │  三级回退: Local Dify → Cloud Dify → DeepSeek   │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │  本地模型服务 (port 8090)                      │      │
│  │  Embedding: BAAI/bge-m3 │ Reranker: Jina v3  │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 选择 | 说明 |
|---|---|---|
| Python 环境 | conda `pyt0` (`/home/lyzhang/miniconda3/envs/pyt0`) | 所有 Python 命令必须使用该环境 |
| 后端框架 | FastAPI + Pydantic v2 | 异步 API，自动 OpenAPI 文档 |
| 数据库 | SQLite (aiosqlite) | 33 张表 + FTS5 全文搜索 |
| ORM | 无（原生 SQL + aiosqlite） | 直接 SQL，通过 repositories 抽象 |
| 前端框架 | Next.js 15.5 (App Router) + React 19 | 教师端 + 学生端双布局 |
| 状态管理 | TanStack Query v5 | 服务端状态缓存 |
| 图表 | ECharts 6.x | 雷达图、趋势线、热力图、柱状图 |
| UI 组件 | shadcn/ui + Tailwind CSS 4 | 原子化样式 |
| 动画 | Framer Motion | 页面过渡 + 树生长动画 |
| Agent 平台 | Dify (本地 + 云端) | LLM 工作流编排、RAG 知识检索 |
| LLM | DeepSeek / GLM | 三级回退（官方→代理→智谱） |
| TTS | Edge-TTS | 语音引导 |
| OCR | PaddleOCR (本地回退) + **百度智能作业批改** (API 主力) | 作业拍照批改 |
| PDF | xelatex + weasyprint + Jinja2 | 作业 PDF + 学生报告 |
| 测试 | pytest / Vitest / Playwright | 后端 341 / 前端 73 / E2E 6 |

## 数据流

### 核心诊断流程

```text
教师输入学生作答 → POST /api/diagnose
  │
  ├─ 规则引擎诊断 (diagnosis.py)
  │   ├─ 解析算式 (ast + operator)
  │   ├─ 逐步验证 (regex + 数值比较)
  │   ├─ 错因编码 (E-K/E-H)
  │   └─ 输出: error_code + confidence + evidence
  │
  ├─ LLM 增强 (可选，via dify_client.py)
  │   ├─ 教师摘要生成
  │   ├─ 学生引导对话
  │   └─ 不改写错因编码
  │
  └─ 教师审核 (review_status: pending_teacher_review)
      ├─ 确认 → 生效
      └─ 驳回 → 标记
```

### 作业全流程

```text
生成作业 (POST /api/homework/generate)
  │  problem_generator.py → 自适应难度 A/B/C
  ▼
布置作业 (POST /api/homework/assign)
  │  → homework_problems + homework_submissions
  ▼
学生作答 (POST /api/homework/submit)
  │  → student_answers + diagnosis_history
  ▼
AI 批改 (POST /api/homework/ai-grade)
  │  grading_service.py → 逐题诊断 + 错因统计
  │  grading_comments → LLM 逐题评语
  ▼
教师审核 → review_status 更新
  ▼
PDF 生成 (POST /api/homework/{id}/generate-pdf)
  │  pdf_service.py → xelatex 编译
  ▼
分析报告 (GET /api/homework/{id}/analytics)
```

### 学生端流程

```text
学生登录 (POST /api/student-auth/login)
  │
  ├─ 仪表盘 (GET /api/students/{id}/dashboard)
  │   └─ 待做作业 + 成长树 + 最近表现
  │
  ├─ 自主练习 (POST /api/students/{id}/practice/start)
  │   └─ start → next → answer → end → 成长更新
  │
  ├─ 扫码批改 (POST /api/homework/{id}/scan-grade)
  │   └─ 拍照 → 百度智能作业批改(主) / 本地OCR(回退) → 提交 → 规则诊断 → 结果
  │   ├─ 百度 API: create_task → poll get_result → 结构化批改
  │   └─ 文档: https://cloud.baidu.com/doc/OCR/s/omimjkvlz
  │
  └─ 课堂测验 (POST /api/quiz/{id}/student-answer)
      └─ 实时答题 + 统计
```

## 核心模块

### 诊断规则引擎 (`services/diagnosis.py`, 34KB)

纯规则引擎，不依赖 LLM 判断算术对错。

- **解析层**: ast.literal_eval + operator 模块解析算式
- **验证层**: 逐步计算 + 数值比较
- **错因编码**: E-K01~E-K23 (知识类) + E-H01~E-H21 (习惯类)
- **输出**: error_code + confidence + evidence + teacher_action

详见 `docs/specs/04_error_taxonomy.md`。

### 题目生成器 (`services/problem_generator.py`, 142KB)

系统中最大的文件。程序化生成数学题：

- 覆盖 E01-E11 所有错因类型的典型题目
- 三级难度: A (基础补救) / B (标准巩固) / C (拓展变式)
- 支持按知识点、错因、题型筛选
- 内置答案计算（保证正确性）

### 批改管道 (`pipeline/grading_pipeline.py`)

节点式处理管道，编排完整批改流程：

```text
homework_gen_node → diagnosis_node → profile_update_node
  → growth_update_node → practice_node → teacher_summary_node
  → student_feedback_builder → response_assembler
```

每个节点独立可测试，通过管道编排器串联。

### Dify 集成 (`services/dify_client.py`, 31KB)

三级回退架构：

1. **本地 Dify** (127.0.0.1:18080) — 首选
2. **云端 Dify** — 备用
3. **DeepSeek 直连** — 兜底

含熔断器 (_CircuitBreaker) 防止级联失败。3 个 Dify App：
- 教师诊断助手
- 学生引导助手
- AI批改画像助手

### 学生掌握度 (`services/mastery_service.py`)

基于 BKT (Bayesian Knowledge Traking) 的掌握度计算：

- 输入: 学生历史答题记录
- 输出: 每个知识点的掌握概率
- 用于: 自适应难度选择 + 薄弱知识点推荐

## 数据库架构

33 张数据表 + 1 个 FTS5 虚拟表。详见 `docs/engineering/data_model.md`。

**核心表分组：**
- 基础实体 (4): students, classes, teachers, academic_cycles
- 作业闭环 (7): homework → homework_problems → homework_submissions → student_answers + homework_pdfs + scanned_submissions + grading_comments
- 诊断错因 (3): diagnosis_history, student_error_stats, student_error_trajectory
- 课堂测验 (4): quiz_sessions, quiz_problems, quiz_responses, quiz_student_answers
- 学生成长 (4): student_cycle_progress, practice_weeks, student_practice_sessions, student_practice_problems
- 教学体系 (3): teaching_units, teaching_schedule, calendar_weeks
- 知识库 (5): knowledge_points, concept_relations, problem_bank, week_calc_mapping, knowledge_points_fts
- 其他 (3): profile_snapshots, exercise_types, error_code_knowledge_map

## 前端架构

Next.js 15.5 App Router，教师端 + 学生端双布局。

```text
web/src/
├── app/
│   ├── (teacher)/          # 教师端路由组 (10 页面)
│   │   ├── login/          # /login
│   │   ├── page.tsx        # / (仪表盘)
│   │   ├── classroom/      # /classroom
│   │   ├── homework/       # /homework
│   │   ├── schedule/       # /schedule
│   │   ├── diagnose/       # /diagnose
│   │   ├── guidance/       # /guidance
│   │   ├── forest/         # /forest
│   │   ├── botanical/      # /botanical
│   │   └── chat/           # /chat
│   ├── (student)/          # 学生端路由组 (7 页面)
│   │   ├── s/login/        # /s/login
│   │   ├── s/home/         # /s/home
│   │   ├── s/growth/       # /s/growth
│   │   ├── s/practice/     # /s/practice
│   │   ├── s/scan/[hwId]/  # /s/scan/:hwId
│   │   ├── s/homework/[id]/# /s/homework/:id
│   │   └── s/quiz/[id]/    # /s/quiz/:id
│   └── (全局)              # loading.tsx, error.tsx, not-found.tsx
├── components/             # 44 个组件
│   ├── forest/             # 森林可视化 (含 Canvas + 粒子系统)
│   ├── classroom/          # 课堂视图
│   ├── homework/           # 作业表单/分析/批改
│   ├── guidance/           # 引导对话
│   ├── diagnose/           # 诊断管道
│   ├── ui/                 # shadcn 基础组件
│   └── layout/             # 导航/页脚/工作台
├── lib/
│   ├── api/                # 集中式 API 客户端 + TanStack Query hooks
│   ├── types/              # TypeScript 类型定义 (504 行)
│   ├── config.ts           # 默认配置 (G6C1 班级, S001 学生)
│   ├── labels.ts           # 中文标签映射
│   └── presentation.ts     # 导航/演示/UI 辅助
```

详见 `docs/engineering/frontend_experience_plan.md`。

## 部署形态

### 开发环境

```text
FastAPI:     http://127.0.0.1:8000
Next.js:     http://127.0.0.1:3000
Local Dify:  http://127.0.0.1:18080
Models:      http://127.0.0.1:8090 (tmux session: models)
SQLite:      ./calc_forest/backend/data/app.db
```

### 生产部署（竞赛演示）

同开发环境，通过 `npx next build --no-lint` 构建前端。

### 学校部署（未来）

```text
内网 Web 服务
PostgreSQL
MinIO 图片存储
国产大模型 API
本地 OCR 或国内 OCR 服务
```

## 合规设计

1. **AI 审核门**: 所有 AI 输出带 `review_status: "pending_teacher_review"`，教师确认后才生效
2. **规则优先**: 算术对错只用规则引擎，LLM 不判断答案对错
3. **合成数据**: 不使用真实学生数据
4. **隐私保护**: 学生使用编号，LLM 只接收脱敏文本
5. **13 岁以下政策**: 教师端 MVP，学生端需教师监督使用

## 后端目录结构

```text
calc_forest/backend/app/
├── main.py              # FastAPI 应用入口 + 路由注册
├── db.py                # 数据库初始化 + 33 张表 DDL
├── schemas.py           # Pydantic 请求/响应模型
├── deps.py              # 依赖注入
├── exceptions.py        # 自定义异常
├── routers/             # 13 个路由器
│   ├── diagnosis.py     # 诊断 + Dify 集成 (6 端点)
│   ├── homework.py      # 作业全流程 (16 端点)
│   ├── student.py       # 学生管理 (10 端点)
│   ├── student_api.py   # 学生端 API (10 端点)
│   ├── quiz.py          # 课堂测验 (6 端点)
│   ├── config.py        # 系统配置 + TTS + PDF (12 端点)
│   ├── curriculum.py    # 教学体系 (6 端点)
│   ├── classroom.py     # 班级视图 (5 端点)
│   ├── knowledge.py     # 知识库 (6 端点)
│   ├── auth.py          # 教师认证 (2 端点)
│   ├── student_auth.py  # 学生认证 (3 端点)
│   ├── ocr.py           # OCR 识别 (4 端点)
│   └── timetable.py     # 课表管理 (6 端点)
├── services/            # 39 个服务模块
│   ├── diagnosis.py     # 规则诊断引擎 (34KB)
│   ├── problem_generator.py # 题目生成器 (142KB)
│   ├── grading_service.py   # AI 批改
│   ├── homework_service.py  # 作业管理
│   ├── llm_client.py        # LLM 三级回退
│   ├── dify_client.py       # Dify 双线路由
│   ├── pdf_service.py       # PDF 生成 (47KB)
│   └── ... (31 more)
├── pipeline/            # 处理管道
│   ├── grading_pipeline.py  # 批改管道编排
│   ├── diagnosis_node.py    # 诊断节点
│   ├── profile_update_node.py
│   ├── growth_update_node.py
│   └── ... (7 more)
├── repositories/        # 数据访问层
│   ├── diagnosis_repo.py
│   ├── homework_repo.py
│   └── stats_repo.py
└── data/                # 数据文件
    └── app.db           # SQLite 数据库
```
