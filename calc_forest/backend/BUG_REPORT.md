# 🐛 Bug Report — 我的计算森林 Backend QA

**Date:** 2026-05-09  
**Tester:** Automated QA  
**Backend:** http://127.0.0.1:8000  
**Data:** 8-week multi-round simulation (10 students × 8 weeks × 5 problems)  

---

## Summary

| Severity | Count |
|----------|-------|
| **P0 (Crash/500)** | 1 |
| **P1 (Wrong Data)** | 7 |
| **P2 (Bad UX/Inconsistency)** | 6 |
| **P3 (Minor)** | 5 |
| **Total** | **19** |

---

## P0 — Crash / Internal Server Error

### BUG-001: `POST /api/quiz/{quiz_id}/response` returns 500 Internal Server Error

**Endpoint:** `POST /api/quiz/QZ3802215E/response`  
**Issue:** Recording a teacher's classroom response to a quiz problem causes a 500 Internal Server Error.  
**Expected:** Returns JSON confirmation or the updated quiz state.  
**Actual:** HTTP 500, Content-Type `text/plain`, body `Internal Server Error`.  
**Evidence:**
```
Request: POST /api/quiz/QZ3802215E/response
Body: {"quiz_id":"QZ3802215E","problem_sequence":1,"class_response":"mostly_correct","notes":"OK"}
Response: 500 Internal Server Error (text/plain)
```
**Fix suggestion:** Check the response handler in `quiz_service.py` for unhandled exceptions. The endpoint schema (`QuizResponseRecord`) expects `quiz_id` (string), `problem_sequence` (integer), `class_response` (string), `notes` (string). The handler likely has a null reference or missing DB column.

---

## P1 — Wrong Data

### BUG-002: `GET /api/classes/{class_id}/summary` returns `total_attempts: 0` despite thousands of diagnosis records

**Endpoint:** `GET /api/classes/G6C1/summary`  
**Issue:** After running multi-round simulation (400+ answers submitted), class summary claims 0 total attempts and 0% accuracy.  
**Expected:** `total_attempts` should reflect actual diagnosis history count, `class_accuracy` should reflect actual average.  
**Actual:**
```json
{"class_id":"G6C1","class_name":"六年级1班","total_students":10,"total_attempts":0,"class_accuracy":0.0,"top_error_tags":[],"students_needing_attention":[]}
```
**Evidence:** S001 profile shows 51 total attempts, S007 shows 16. The summary should aggregate these.  
**Fix suggestion:** The `class_service.py` summary query likely reads from `diagnosis_history` with a filter that doesn't match. Check if it filters by `class_id='CLS001'` instead of `'G6C1'`, or if it only reads from a different table.

### BUG-003: `GET /api/students/{id}/profile` accuracy disagrees with `GET /api/classes/{id}/forest`

**Endpoints:** `/api/students/S001/profile` vs `/api/classes/G6C1/forest`  
**Issue:** S001 profile accuracy = 0.2549, but forest view shows 0.5729 for the same student.  
**Expected:** Both endpoints should report the same accuracy for the same student.  
**Actual:** Profile says 25.5%, forest says 57.3% — more than 2× difference.  
**Fix suggestion:** Forest and profile likely compute accuracy from different data sources. Unify the calculation or have forest reference the same profile data.

### BUG-004: `GET /api/classes/{id}/forest` returns wrong cycle (`CYC_2025_2026_S1`) instead of current (`CYC_2025_2026_S2`)

**Endpoint:** `GET /api/classes/G6C1/forest`  
**Issue:** Forest view shows `cycle_id: "CYC_2025_2026_S1"` but the current cycle is `CYC_2025_2026_S2`. All simulation data was created in S2 context.  
**Expected:** Forest should show the current cycle or accept a cycle parameter.  
**Actual:** `cycle_id: "CYC_2025_2026_S1"` — wrong semester.  
**Fix suggestion:** `forest_service.py` likely hard-codes or defaults to S1. Should use `cycle_service.py` to get the current cycle.

### BUG-005: `GET /api/students/{id}/trajectory` returns empty array for all students

**Endpoint:** `GET /api/students/S001/trajectory`, `GET /api/students/S007/trajectory`  
**Issue:** After 8 weeks of simulation with homework submissions and grading, the error trajectory is empty.  
**Expected:** Per-unit error trajectory showing accuracy trends across weeks.  
**Actual:** `[]` (empty array) for all students.  
**Evidence:** S001 has 51 diagnosis records, S007 has 16. The trajectory should have data.  
**Fix suggestion:** `curriculum_service.py` trajectory query may not join correctly with the data that the simulation creates, or the trajectory table is never populated by the grading pipeline.

### BUG-006: `GET /api/students/{id}/growth` shows inconsistent data — some students have `days_completed: 0` despite active simulation

**Endpoints:** `/api/students/S005/growth`, `/api/students/S007/growth`  
**Issue:** After 8-week simulation, S005 and S007 growth shows `days_completed: 0, current_stage: "seed", tree_species_id: null`. But S001 and S002 show proper growth (days_completed=15/20, stage=taller/sapling, species assigned).  
**Expected:** All 10 students should have non-zero days_completed after 8 weeks of simulation.  
**Actual:**
```json
S005: {"days_completed":0,"current_stage":"seed","tree_species_id":null}
S007: {"days_completed":0,"current_stage":"seed","tree_species_id":null}
S001: {"days_completed":15,"current_stage":"taller","tree_species_id":"apple"}
```
**Fix suggestion:** Growth update logic in the grading pipeline doesn't consistently update all students. Some students' `student_cycle_progress` rows may not be initialized correctly.

### BUG-007: `GET /api/classes/{id}/forest` shows all students at `stage: "seed"` and `days_completed: 0`

**Endpoint:** `GET /api/classes/G6C1/forest`  
**Issue:** Forest view shows every student at `current_stage: "seed"`, `days_completed: 0`. But individual growth endpoint shows S001 at `stage: "taller"` with 15 days.  
**Expected:** Forest view should reflect the same growth data as individual growth endpoint.  
**Actual:** All 10 students at seed/0 days in forest.  
**Fix suggestion:** Forest likely queries `student_cycle_progress` for cycle `CYC_2025_2026_S1` (wrong cycle — see BUG-004), while growth endpoint queries S2.

### BUG-008: Homework `class_id` inconsistency — homework uses `CLS001`, students use `G6C1`

**Endpoint:** `POST /api/homework/generate` with `class_id: "CLS001"`  
**Issue:** The old `simulate_multiround.py` script and the AGENTS.md documentation use `CLS001` as class_id, but the actual class_id in the database is `G6C1`. This means homework generated with `CLS001` won't appear in forest/class views that filter by `G6C1`.  
**Expected:** Consistent class_id across all entities.  
**Actual:** Students have `class_id: "G6C1"`, homework from simulation has `class_id: "CLS001"`.  
**Fix suggestion:** Standardize on `G6C1` everywhere. Update `simulate_multiround.py` and any reference data. Alternatively, ensure class lookup is flexible.

---

## P2 — Bad UX / Inconsistency

### BUG-009: `POST /api/homework/generate` response schema inconsistency

**Endpoint:** `POST /api/homework/generate`  
**Issue:** When called with `student_ids`, returns `{"homework_id": "HW...", "problem_count": 5, "error_codes_target": [...]}` (3 fields). When called without `student_ids`, returns full homework object with `id` (not `homework_id`), plus all fields including embedded `problems[]`.  
**Expected:** Consistent response schema regardless of parameters.  
**Actual:** Two completely different response shapes:
```json
// With student_ids:
{"homework_id":"HW1927F921","problem_count":5,"error_codes_target":["E03"]}

// Without student_ids:
{"id":"HWBF171A30","class_id":"G6C1","problems":[...],"status":"draft",...}
```
**Fix suggestion:** Standardize on the full object response. Always return `id` and embed `problems`.

### BUG-010: `GET /api/students/{id}` returns `id` not `student_id`

**Endpoint:** `GET /api/students/S001`  
**Issue:** Response field is `id` not `student_id`. AGENTS.md and likely the frontend expect `student_id`.  
**Expected:** `{"student_id": "S001", "name": "王子涵", ...}`  
**Actual:** `{"id": "S001", "name": "王子涵", ...}`  
**Fix suggestion:** Rename `id` to `student_id` in the response schema, or add `student_id` as an alias.

### BUG-011: `GET /api/tree-species` uses `id` not `species_id`

**Endpoint:** `GET /api/tree-species`  
**Issue:** AGENTS.md says species have `species_id`. Response uses `id`.  
**Expected:** `{"species_id": "apple", "name": "苹果树", ...}`  
**Actual:** `{"id": "apple", "name": "苹果树", ...}`  
**Fix suggestion:** Rename `id` to `species_id` for consistency with AGENTS.md.

### BUG-012: `POST /api/diagnose` requires `grade` as required field — API docs say `expression`/`student_answer`

**Endpoint:** `POST /api/diagnose`  
**Issue:** AGENTS.md documents the request as `{expression, student_answer}`, but the actual schema requires `grade`, `problem`, `correct_answer`, `student_answer`. The field names `expression` and `student_answer` from docs don't match `problem` and `correct_answer` in the actual API.  
**Expected:** AGENTS.md accurately documents the required fields.  
**Actual:** Required: `["grade", "problem", "correct_answer", "student_answer"]` — none of `expression`, and `correct_answer` is required (meaning the teacher/system must know the answer).  
**Fix suggestion:** Update AGENTS.md to reflect actual schema. Consider making `correct_answer` optional (auto-compute from `problem`).

### BUG-013: `POST /api/homework/submit` answers use `Dict[str,str]` — `problem_sequence` must be string not integer

**Endpoint:** `POST /api/homework/submit`  
**Issue:** The `answers` array items are typed as `additionalProperties: {type: string}` meaning ALL fields including `problem_sequence` must be strings. Natural expectation is integer for sequence.  
**Expected:** `problem_sequence` should accept integer.  
**Actual:** Sending `problem_sequence: 1` → 422 validation error. Must send `"1"` (string).  
**Fix suggestion:** Define a proper `HomeworkAnswerItem` Pydantic model with `problem_sequence: int` and `raw_answer: str`.

### BUG-014: Knowledge search returns empty snippets

**Endpoint:** `GET /api/knowledge/search?q=退位`  
**Issue:** Search results have `snippet: ""` for all matches. No preview text is returned.  
**Expected:** Snippet should contain a relevant excerpt from the matched document.  
**Actual:** `"snippet": ""` for every result.  
**Fix suggestion:** FTS5 `snippet()` or `highlight()` function is not being applied in the query, or the `snippet` column is not populated. Check `knowledge_service.py`.

---

## P3 — Minor

### BUG-015: `GET /api/students/{id}/profile` has no `error_stats` key

**Endpoint:** `GET /api/students/S001/profile`  
**Issue:** AGENTS.md documents `error_stats` as a key in the profile response. The actual response uses `accuracy_by_error_code` instead.  
**Expected:** `error_stats` key present.  
**Actual:** Key is `accuracy_by_error_code`, not `error_stats`.  
**Fix suggestion:** Either add `error_stats` as an alias or update AGENTS.md.

### BUG-016: `GET /api/curriculum/schedule/CLS001` returns empty — must use `G6C1`

**Endpoint:** `GET /api/curriculum/schedule/CLS001`  
**Issue:** Using the documented `CLS001` returns `[]`. Must use `G6C1` to get the 18-week schedule.  
**Expected:** Either `CLS001` works or documentation uses `G6C1`.  
**Actual:** Empty array with `CLS001`, full schedule with `G6C1`.  
**Fix suggestion:** Update AGENTS.md to use `G6C1`, or add `CLS001` as an alias.

### BUG-017: Diagnosis returns student_id `S000` when student_id not provided

**Endpoint:** `POST /api/diagnose`  
**Issue:** When `student_id` is omitted from the request, the response shows `student_id: "S000"` instead of `null`.  
**Expected:** `student_id: null` when not provided.  
**Actual:** `student_id: "S000"` — a fake student ID.  
**Fix suggestion:** Default to `null` or omit the field when no student_id is provided.

### BUG-018: `POST /api/homework/grade` returns only `E08` (步骤遗漏) for all wrong answers

**Endpoint:** `POST /api/homework/grade`  
**Issue:** When all 3 answers are wrong (submitted "999" for fraction problems like `6÷2/5=`), grading only returns `E08` (步骤遗漏/missing steps). It should detect more specific errors like E01 (基础事实错误) or E07 (运算顺序错误).  
**Expected:** More specific error classification based on the actual problem and answer.  
**Actual:** `primary_errors: ["E08"]` for every wrong answer regardless of problem type.  
**Fix suggestion:** The grading pipeline should pass each answer through the full diagnosis engine, not just default to E08 when no steps are provided.

### BUG-019: Quiz response endpoint schema mismatch — `class_response` field name differs from documented `teacher_response`

**Endpoint:** `POST /api/quiz/{quiz_id}/response`  
**Issue:** AGENTS.md documents the body as `{teacher_response, notes}`, but the actual schema (`QuizResponseRecord`) uses `class_response` as the field name.  
**Expected:** Field name matches documentation.  
**Actual:** Schema uses `class_response`, not `teacher_response`.  
**Fix suggestion:** Align naming — either update docs or add `teacher_response` as alias.

---

## Test Pass Rate

| Category | Tested | Passed | Failed |
|----------|--------|--------|--------|
| Core CRUD (health, student, class) | 5 | 3 | 2 |
| Diagnosis | 6 cases | 6 | 0 (schema mismatch counted separately) |
| Homework lifecycle | 5 | 3 | 2 |
| Quiz lifecycle | 4 | 2 | 2 |
| Curriculum | 3 | 3 | 0 |
| Knowledge search | 1 | 1 | 0 |
| Config endpoints | 2 | 2 | 0 |
| Reports | 2 | 2 | 0 |
| Cross-endpoint consistency | 5 | 1 | 4 |
| **Total** | **33** | **23** | **10** |

---

## Critical Path for Competition Demo

The following bugs would be **most embarrassing** in a live demo and should be fixed first:

1. **BUG-001** (P0): Quiz response crashes — this is the core classroom flow
2. **BUG-004** (P1): Forest shows wrong cycle — immediately visible on homepage
3. **BUG-002** (P1): Class summary shows 0 data — dashboard looks broken
4. **BUG-003** (P1): Accuracy mismatch between profile and forest — trust issue
5. **BUG-009** (P2): Homework generate inconsistent response — frontend integration nightmare
6. **BUG-012** (P2): Diagnosis API docs wrong — any demo script will fail
7. **BUG-008** (P1): class_id CLS001 vs G6C1 — cascading data isolation
