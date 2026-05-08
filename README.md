# Teaching Agent

《创AI》小学数学教育智能体项目，当前产品名为 **我的计算森林**（原名 **计算小树苗**）。

这是一个 **Dify-first** 的成长型教育智能体：教师在短时间内得到可审核的诊断与练习草案，孩子在 3 到 5 分钟的练习里看见自己的长期成长，而不是被排名和打卡压力驱动。

Start here:

1. Read `Agent.md` for session handoff and current project rules.
2. Read `docs/README.md` for the document-side map.
3. Read `docs/project_management/task_board.md` for current work.
4. Use `development/` for code, tests, and demo data.
5. Use `calc_forest/` for future product implementation and standalone git-managed work.

## Current Build Direction

```text
teacher enters a short answer record
  -> Dify workflow calls FastAPI tools
  -> diagnosis + guided practice draft return
  -> teacher reviews before classroom or student use
  -> future product layer shows gentle forest-style growth feedback
```

The current MVP remains teacher-side first. Full student app, parent app, OCR, complete textbook graph, and complete holiday workflows are future scope unless explicitly requested.

The broader product vision already incorporates the 2026-05-02 teacher revision:
- each semester or holiday grows one tree
- across primary school years, trees accumulate into a forest
- guidance stays textbook-aligned and does not dump answers
- multimodal input is a planned direction, not an MVP blocker

## Workspace Layout

| Directory | Purpose |
| --- | --- |
| `docs/` | Document-side workspace: specs, engineering, research, operations, competition material, source material, and legacy notes |
| `development/` | Development-side workspace: FastAPI app, tests, and synthetic demo data |
| `calc_forest/` | Product-side workspace for the future 我的计算森林 application and standalone git management |

For the full document breakdown, see `docs/README.md`.

## Runtime

Default Python environment:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python
```

## Test

Current environment has shown occasional pytest capture temp-file issues, so use `-s`:

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

Current expected result:

```text
11 passed
```

## Run API

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Diagnosis API:

```bash
curl -X POST http://127.0.0.1:8000/api/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S001",
    "grade": 4,
    "problem": "402-178=",
    "correct_answer": "224",
    "student_answer": "334",
    "student_steps": []
  }'
```

## Current Error Coverage

`POST /api/diagnose` currently supports first-pass diagnosis for:

- `E01` 基础事实错误
- `E02` 进位错误
- `E03` 退位错误
- `E04` 数位对齐错误
- `E05` 运算顺序错误
- `E06` 小数点/分数单位错误
- `E07` 抄题/转写错误
- `E08` 步骤遗漏
- `E11` 未验算

Every diagnosis defaults to `pending_teacher_review`.

## Current Implemented APIs

- `GET /health`
- `POST /api/diagnose`
- `POST /api/practice/recommend`
- `GET /api/tree-species`
- `GET /api/encouragements`
- `POST /api/dify/session-draft`

## Next Focus

- Keep `Agent.md` current whenever paths, APIs, test commands, or scope change.
- Build the Dify-first product shell around the existing FastAPI tools.
- Strengthen the known diagnosis gaps documented in `docs/specs/02_mvp_scope.md`.
- Prepare 2-3 complete diagnosis cases for competition/demo credibility in `docs/competition/`.
