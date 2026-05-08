# Teaching Agent Handoff

## Current Project

This project is building **我的计算森林** (formerly 计算小树苗), an education agent for primary-school math calculation diagnosis, guided practice, and teacher-reviewed feedback.

Competition direction: 《创AI》 / 教育智能体.

Current external positioning: Dify-first teacher workbench for diagnosis, guidance, and short targeted practice, with forest language retained only as brand/tone.

Current engineering focus: **Dify-first teacher-side MVP**. Do not expand implementation to a full student app, parent app, long-term student growth system, full textbook system, OCR pipeline, or heavy game economy unless the task explicitly says so.

## Current MVP

MVP chain:

```text
synthetic answer record -> Dify/teacher workbench -> FastAPI diagnosis API -> error tag + evidence + guided feedback -> teacher review
```

Current API (17 endpoints):

- `GET /health`
- `POST /api/diagnose`
- `POST /api/practice/recommend`
- `GET /api/tree-species`
- `GET /api/encouragements`
- `POST /api/dify/session-draft`
- `POST /api/dify/full-pipeline`
- `GET /api/students/{student_id}`
- `GET /api/students/{student_id}/profile`
- `GET /api/students/{student_id}/growth`
- `GET /api/classes/{class_id}`
- `GET /api/classes/{class_id}/summary`
- `GET /api/cycles/current?grade=`
- `POST /api/homework/generate`
- `POST /api/homework/assign`
- `POST /api/homework/submit`
- `POST /api/homework/grade`
- `GET /api/knowledge/search?q=`

Data layer: SQLite via `aiosqlite` (WAL mode), DB at `development/data/calc_forest.db`.
Seed script: `development/scripts/seed_data.py`. Homework simulator: `development/scripts/simulate_homework.py`.
Knowledge base: `development/data/knowledge/` (FTS5 indexed).

Pipeline architecture: `development/app/pipeline/` (BaseNode → Pipeline orchestrator, 6 nodes).

New data models designed (specs, not yet in code):

- Guidance modes (standard/exploration/challenge)
- Growth/tone-layer data (milestones, tree species, encouragement templates) reserved for brand expression and later expansion

Implemented data models (in code, backed by SQLite):

- Student + StudentProfile
- Class + ClassSummary
- AcademicCycle + StudentCycleProgress
- DiagnosisRecord (persistent history)
- Long-term roadmap: `docs/project_management/roadmap.md`

See `docs/specs/08_forest_growth_system.md`, `docs/specs/09_guidance_system.md`, `docs/specs/10_multimodal_input.md`.

Current development root:

- `/mnt/d/Ubuntu_WSL/Teaching_agent/development`

## Highest-Priority Rules

1. Teacher review comes first. AI output is always a draft or recommendation, never directly published to students.
2. MVP covers primary calculation diagnosis for grades 1-6. Do not implement a full textbook graph yet.
3. Do not create rankings, forced streaks, holiday pressure, or parent pressure.
4. Use only synthetic or anonymized demo data.
5. Do not let an LLM decide arithmetic correctness. Rules/API produce structured diagnosis; LLM may only explain or summarize.
6. Error guidance walks the child through thinking (4-step method), never dumps the answer.
7. Keep competition vision separate from implemented MVP.
8. Forest-related wording is brand/tone by default, not proof of current MVP scope.

## Current First-Version Scope

First-version problem types:

- 20以内加减法（1-2年级口算）— *planned*
- 表内乘除法（2-3年级）— *planned*
- Three-digit addition/subtraction.
- Continuous borrowing subtraction with zero.
- One-digit multiplied by two-digit numbers.
- Simple mixed operations.

Current error codes use `E01-E11`; `docs/specs/04_error_taxonomy.md` is the PM-facing source of truth.

Guidance system: 4-step method (comfort → reasoning → summary → practice), three modes (standard/exploration/challenge). See `docs/specs/09_guidance_system.md`.

## Runtime

Python environment:

```bash
/home/lyzhang/miniconda3/envs/pyt0/bin/python
```

Run tests:

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

Run API locally:

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Key Entrypoints

- `README.md`: repository overview.
- `docs/README.md`: document-side map and reading guide.
- `docs/DOC_ALIGNMENT_MAP.md`: document alignment hub and sync-trigger map.
- `docs/specs/`: PM-reviewable product planning and acceptance docs.
- `development/`: code, tests, and demo data.
- `calc_forest/`: future product workspace for the brand-facing application.
- `calc_forest/dify/`: Dify product workspace and nightly build assets.
- `docs/project_management/task_board.md`: current task board.
- `docs/project_management/decision_log.md`: major decisions.
- `docs/project_management/session_protocol.md`: session workflow.
- `docs/source_materials/teacher_feedback/`: original teacher-authored feedback, including the 计算小树苗 design document.
- `docs/competition/`: competition report/script/form/evidence material.

## Do Not Do By Default

- Do not use real student data.
- Do not make OCR a blocker for MVP.
- Do not implement complete student/parent/holiday products ahead of the teacher MVP.
- Do not turn the tree-growth concept into a heavy game system.
- Do not treat long-term forest accumulation as the current product center.
- Do not treat competition vision as shipped functionality.
- Do not change directory structure without updating this file, `README.md`, `docs/README.md`, and `docs/project_management/task_board.md`.

## Session Startup

Each new Codex session should:

1. Read this file first.
2. Read `docs/project_management/task_board.md` and `docs/project_management/decision_log.md`.
3. Read `docs/DOC_ALIGNMENT_MAP.md` before making cross-doc or code/doc consistency changes.
4. Identify the session type: exploration, exploitation, or validation.
5. Confirm the write scope before editing.
6. Run relevant tests or document why they were not run.

## Session Shutdown

Before final response:

1. List changed files.
2. Report verification commands and results.
3. Update `docs/project_management/task_board.md` if task status changed.
4. Update `docs/DOC_ALIGNMENT_MAP.md` if source-of-truth files, sync triggers, or directory responsibilities changed.
5. Update this file when scope, paths, APIs, or test commands change.

## Latest Status

- Project rebranded to **我的计算森林** (formerly 计算小树苗).
- Project structure currently has three active roots: `docs/`, `development/`, and `calc_forest/`.
- `docs/` contains `specs/`, `engineering/`, `research/`, `project_management/`, `competition/`, `source_materials/`, and legacy `product/` notes.
- FastAPI MVP currently lives under `development/app`.
- Demo data lives under `development/data/demo_answer_records.json`.
- Tests live under `development/tests`.
- `calc_forest/` is reserved for future product-side implementation and separate git-managed work.
- Current implemented API set includes diagnosis, practice recommendation, teacher-side class/student endpoints, tree-species config, encouragement config, and a Dify-ready combined session draft endpoint.
- All Python commands must use the `pyt0` environment.
- Current tests: `11 passed`.
- Current synthetic data: 24 answer records, 5 anonymized students, grades 3-6 (expanding to 1-6).
- Known rule gaps: one mixed-operation parenthesis case and one two-digit multiplication partial-product alignment case remain for diagnosis-rule enhancement.
- New specs added (not yet in code): `08_forest_growth_system.md`, `09_guidance_system.md`, `10_multimodal_input.md`.
- Forest/tone-layer assets remain designed, but are no longer the current MVP's main narrative.
- Guidance modes and encouragement templates designed.
