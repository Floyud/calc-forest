# Backend — 我的计算森林

FastAPI 后端，提供错因诊断、作业批改、学生画像等 API 服务。

## Contents

| Path | Purpose |
| --- | --- |
| `app/` | FastAPI 应用（路由、服务、数据库） |
| `tests/` | 后端测试（341 passed） |
| `scripts/` | 种子数据、模拟脚本 |
| `data/` | SQLite 数据库、模板、静态资源 |
| `templates/` | PDF 生成模板 |

## Runtime

Use `pyt0`:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python
```

## Test

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/ -q --ignore=tests/test_e2e_smoke.py --ignore=tests/test_dify_e2e.py -k "not full_pipeline"
```

## Run API

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

详细 API 列表见项目根目录 `AGENTS.md`。
