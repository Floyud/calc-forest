# Teaching Agent

《创AI》小学数学教育智能体项目，产品名 **我的计算森林**。

**AI批阅，教师把关。** AI自动批改作业并诊断错因，教师审核确认后生效。

## Start Here

1. `AGENTS.md` — 项目架构、命令、约束、文档总索引
2. `docs/project_management/task_board.md` — 当前任务状态
3. `docs/specs/04_error_taxonomy.md` — E01-E11 错因体系（核心）
4. `docs/competition/demo_video_script_v2.md` — 竞赛演示脚本

## Workspace Layout

| Directory | Purpose |
| --- | --- |
| `calc_forest/backend/` | FastAPI 后端、测试、脚本、模拟数据 |
| `calc_forest/web/` | Next.js 前端 |
| `calc_forest/dify/` | Dify 工作流 DSL |
| `docs/` | 产品文档、工程文档、竞赛材料 |
| `knowledge_base/` | Dify 知识库源文件（本地=source of truth） |
| `给mom看的/` | 教师端用户文档 |

## Quick Start

### 后端

```bash
cd calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/ -q --ignore=tests/test_e2e_smoke.py --ignore=tests/test_dify_e2e.py -k "not full_pipeline"
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd calc_forest/web
npm run dev                              # 开发服务器 (port 3002)
npx next build --no-lint                 # 生产构建
```

### 模拟数据

```bash
cd calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_realistic.py
```

## Runtime

- Python: `/home/lyzhang/miniconda3/envs/pyt0/bin/python`
- Node: Next.js 15.5 App Router
- DB: SQLite (FTS5)
- Charts: ECharts 6.x
- LLM: DeepSeek/GLM 三级回退
- Dify: 本地 (port 18080) + 云端回退
