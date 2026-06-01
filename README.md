<div align="center">

# 🌲 我的计算森林

**AI批阅，教师把关** — 小学数学计算错因诊断智能体

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

> 《创AI》竞赛参赛作品 · 面向小学数学教学场景的 Dify-first 教育智能体

## 为什么做这个

小学数学计算教学有一个核心痛点：**老师知道学生错了，但不知道为什么错。**

传统批改只能回答"对"或"错"。但同样一道减法题做错，原因可能是：
- **退位错误**（个位不够减，忘了从十位借 1）
- **基础事实错误**（口诀背错了）
- **数位对齐错误**（竖式写歪了）
- **未验算**（算完没检查）

这些错因的教学对策完全不同。把所有错误都归为"粗心"，是教学资源的浪费。

**我的计算森林** 做的就是这件事：告诉老师**错在哪里、为什么错、下一步该怎么教**。

## 产品核心

### 🔬 纳米级错因诊断

自研 **E-K01~E-K23 + E-H01~E-H21** 共 44 种错因分类体系（知识类 23 种 + 习惯类 21 种），是目前国内小学数学领域最精细的诊断分类。

诊断引擎基于**纯规则**（regex + AST/operator 分析），不依赖 LLM 判断对错，结果可解释、可复现。LLM 仅用于生成评语和教学建议。

### 👩‍🏫 教师审核门控

所有 AI 输出默认标记为 `pending_teacher_review`。教师确认后才生效——**AI 是助手，教师是决策者**。

这不仅是产品理念，更是对 2025 年教育部"13 岁以下学生不得独立使用生成式 AI"政策的原生合规。

### 🌱 引导不倒答案

学生端使用**四步引导法**（安慰→推理→归纳→练习），通过 Edge-TTS 语音一步步引导学生自己想明白。永远不直接给出答案。

### 📊 作业全生命周期

```
生成 → 布置 → 提交 → AI批改 → 教师审核 → PDF/报告 → 针对性练习
```

支持自适应难度（A/B/C 三档），程序化出题覆盖 E01-E11 全部错因，无限供应。

### 🌳 成长型反馈

每个孩子种一棵树，做对题就长高。没有排名，没有打卡压力，没有家长端的焦虑推送——只有一片森林，记录每个孩子的成长。

## 技术架构

```
┌─────────────────────────────────────────────┐
│              教师端 (Next.js)                │
│  森林看板 · 作业闭环 · 诊断演示 · 课表管理    │
├─────────────────────────────────────────────┤
│              学生端 (Next.js)                │
│  仪表盘 · 自主练习 · 扫码批改 · 课堂测验      │
├─────────────────────────────────────────────┤
│            FastAPI 后端 (~75 端点)            │
│  13 路由器 · 30+ 服务 · 批改管道 · BKT掌握度  │
├─────────────────────────────────────────────┤
│           AI / LLM 集成层                    │
│  Dify 三级回退 · DeepSeek/GLM · RAG 知识检索  │
├─────────────────────────────────────────────┤
│           SQLite (33 表 + FTS5)              │
└─────────────────────────────────────────────┘
```

### 后端

| 模块 | 说明 |
|---|---|
| 13 个路由器 | 作业、学生、测验、诊断、知识库、OCR、课表、认证等 |
| 规则诊断引擎 | 纯逻辑判断（regex + AST），覆盖 44 种错因 |
| 程序化出题器 | 142KB，A/B/C 三级难度，按错因代码精准出题 |
| 批改管道 | 11 个节点模块，编排诊断→画像→成长→练习推荐 |
| BKT 掌握度 | 贝叶斯知识追踪，量化每个知识点掌握概率 |
| PDF 生成 | xelatex + weasyprint，支持作业单和班级报告 |
| 百度 OCR | 智能作业批改 API（拍照识别 + 自动批改） |
| Edge-TTS | 语音引导合成，步骤化引导不倒答案 |
| 341 个测试 | pytest 覆盖诊断、批改、管道、API 端点等 |

### 前端

| 模块 | 说明 |
|---|---|
| 教师端 | 森林看板、作业闭环、课堂模式、诊断演示、课表、引导对话 |
| 学生端 | 仪表盘、成长树、自主练习、扫码批改、作业、测验 |
| 可视化 | ECharts 6.x（雷达图、热力图、趋势线）+ Canvas 森林渲染器 + 粒子系统 |
| 17 个页面路由 | Next.js 15.5 App Router，双布局隔离 |

### AI 集成

| 层级 | 回退链 |
|---|---|
| Dify | 本地 (port 18080) → 云端 → DeepSeek 直连 |
| LLM | DeepSeek 官方 → 代理 → 智谱 GLM |
| 本地模型 | BAAI/bge-m3 (Embedding) + jina-reranker-v3 (Reranker) |
| 知识库 | 147 个中文 Markdown 文件，覆盖 1~6 年级知识点 |

## 项目结构

```
calc_forest/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── routers/      # 13 个路由器
│   │   ├── services/     # 30+ 服务模块
│   │   ├── pipeline/     # 批改管道（11 节点）
│   │   └── repositories/ # 数据访问层
│   ├── tests/            # 341 个测试
│   └── scripts/          # 种子数据、模拟器
├── web/                  # Next.js 前端
│   └── src/
│       ├── app/(teacher)/  # 教师端页面
│       ├── app/(student)/  # 学生端页面
│       └── components/     # 44 个组件
└── dify/                 # Dify 工作流 DSL

docs/                     # 产品文档、工程文档、竞赛材料
knowledge_base/           # 147 个知识库文件（1~6 年级）
```

## Quick Start

### 环境要求

- Python 3.11+（推荐 conda 环境）
- Node.js 18+（推荐 20+）
- SQLite 3（内置）

### 后端

```bash
cd calc_forest/backend
pip install -r requirements.txt

# 运行测试
pytest -s tests/ -q --ignore=tests/test_e2e_smoke.py --ignore=tests/test_dify_e2e.py -k "not full_pipeline"

# 启动 API
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd calc_forest/web
npm install

npm run dev                # 开发服务器
npx next build --no-lint   # 生产构建
```

### 模拟数据

```bash
cd calc_forest/backend
python scripts/simulate_realistic.py   # 8 周真实感模拟（3 档学生、自适应难度）
```

### 环境变量

复制 `.env.example` 为 `.env`，填入实际 API 密钥：

```bash
cp .env.example .env
```

需要的密钥：DeepSeek API Key、智谱 GLM API Key、Dify 配置（可选）。

## 核心约束

| 约束 | 说明 |
|---|---|
| 算术对错只用规则引擎 | LLM 可总结或解释，但**绝不能**判断答案对错 |
| 教师审核门 | 所有 AI 输出必须经教师确认，绝不能绕过 |
| 引导不倒答案 | 步骤引导思考过程，永远不直接给出答案 |
| 合成数据 | 不使用真实学生数据，演示全部使用模拟数据 |
| 无排名、无打卡 | 成长型反馈，不制造焦虑 |

## 文档导航

| 文档 | 说明 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 项目架构、命令、约束、文档总索引 |
| [`docs/specs/04_error_taxonomy.md`](docs/specs/04_error_taxonomy.md) | 44 种错因分类体系（E-K/E-H） |
| [`docs/engineering/architecture.md`](docs/engineering/architecture.md) | 系统架构总览（端点清单、数据流） |
| [`docs/competition/demo_video_script_v2.md`](docs/competition/demo_video_script_v2.md) | 竞赛演示脚本 |
| [`docs/project_management/task_board.md`](docs/project_management/task_board.md) | 当前任务状态 |

## License

MIT
