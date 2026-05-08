# Development

Development-side workspace for the MVP backend.

当前方向：为 Dify-first 的“我的计算森林”提供本地可测的工具 API。

## Contents

| Path | Purpose |
| --- | --- |
| `development/app/` | FastAPI app and diagnosis services |
| `development/tests/` | Backend tests |
| `development/data/` | Synthetic demo data and test fixtures |

## Runtime

Use `pyt0`:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python
```

## Test

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

## Run API

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Current API:

- `GET /health`
- `POST /api/diagnose`
- `POST /api/practice/recommend`
- `GET /api/tree-species`
- `GET /api/encouragements`
- `POST /api/dify/session-draft`
