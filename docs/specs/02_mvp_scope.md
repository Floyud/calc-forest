# MVP Scope

## In Scope

- FastAPI backend under `development/app`.
- Synthetic demo data under `development/data`.
- Teacher workbench flow built around Dify-first interaction and teacher review.
- Diagnosis endpoint: `POST /api/diagnose`.
- Practice recommendation endpoint: `POST /api/practice/recommend`.
- Tree-species config endpoint: `GET /api/tree-species`.
- Encouragement config endpoint: `GET /api/encouragements`.
- Dify combined draft endpoint: `POST /api/dify/session-draft`.
- Health endpoint: `GET /health`.
- Error tags using `E01-E11`.
- First-version calculation scenarios:
  - 20以内加减法（1-2年级口算）.
  - 表内乘除法（2-3年级）.
  - Three-digit addition/subtraction.
  - Continuous borrowing subtraction with zero.
  - One-digit multiplied by two-digit numbers.
  - Simple mixed operations.
- Teacher-review status on every diagnosis result.
- Four-step guidance method (comfort → reasoning → summary → practice).
- Growth milestone data model as reserved brand/tone layer (see `docs/specs/08_forest_growth_system.md`).
- Tree species data as optional tone/config data (8 core species, see `docs/specs/08_forest_growth_system.md`).
- Encouragement templates as optional tone/config data.
- Guidance mode field in API models (`standard` / `exploration` / `challenge`).
- Tests for correct answer, carry, borrow, operation order, basic fact, and API/config response.

## Out of Scope

- Full OCR (photo upload remains future).
- Real student data.
- Full student app (front-end remains mock/synthetic).
- Parent app.
- Complete textbook knowledge graph.
- Voice input (ASR integration).
- Heavy tree-growth animation, forest accumulation UX, or game economy.
- Full Dify/Coze deployment.
- 30+ tree species full knowledge cards (MVP does 8).
- Six-year persistent user system / graduation album.
- Multi-textbook-version support beyond 人教版.

## Current Evidence

- 24 synthetic answer records.
- 5 anonymized students: `S001-S005`.
- Grade coverage: 1-6 (expanding from initial 3-6).
- 8 core tree species defined.
- Tree species config and encouragement config added to `development/data`.
- Growth milestone system designed (9 stages), but not treated as current MVP center.
- Four-step guidance method designed.
- Three guidance modes designed (standard/exploration/challenge).
- Current test result: `11 passed`.
- Current synthetic-data primary-tag match: 22/24.

## Known Gaps

- Mixed-operation parenthesis step error needs stronger `E05` handling.
- Two-digit multiplication partial-product alignment needs stronger `E04/E08` handling.
- 1-2 grade oral calculation diagnosis rules not yet implemented.
- Growth milestone logic is not yet connected to persistent student records.
- Forest view and long-term growth narrative are not current MVP priorities.
- Engineering docs should continue to align around the expanded Dify-ready tool set.
