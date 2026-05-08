# Evaluation Plan

## Current Test Command

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```

Expected current result:

```text
11 passed
```

## Current Dataset Check

Dataset:

```text
development/data/demo_answer_records.json
```

Current properties:

- 24 synthetic records.
- 5 anonymized students: `S001-S005`.
- Grades 3-6.
- Required fields present.
- Primary diagnosis matches one expected tag for 22/24 records.

## Unit Test Coverage

Current tests cover:

- Correct answer -> `OK`.
- Carry error -> `E02`.
- Borrow error -> `E03`.
- Operation order error -> `E05`.
- Basic fact error -> `E01`.
- API response shape and `pending_teacher_review`.
- Practice recommendation and tree-species config endpoints.

## Known Failing/Gapped Cases

1. `R0018`: mixed operation with parentheses and inconsistent intermediate steps.
2. `R0021`: two-digit multiplication partial-product alignment/merge issue.

These should become regression tests after rule enhancement.

## Acceptance Bar For Next Build

- Keep unit tests passing.
- Add tests for `R0018` and `R0021` once behavior is defined.
- Keep diagnosis evidence teacher-readable.
- Do not increase false positives for `E07` transcription errors.
