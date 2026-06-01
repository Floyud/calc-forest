# Demo Answer Records

`demo_answer_records.json` contains 24 synthetic elementary arithmetic answer records for local demos and tests.

Each record includes:

- `record_id`
- `student_id`
- `grade`
- `class_id`
- `knowledge_point`
- `problem`
- `correct_answer`
- `student_answer`
- `student_steps`
- `expected_error_tags`
- `source`
- `time_spent_seconds`
- `is_synthetic`

The dataset covers students `S001` through `S005`, grades 3 through 6, and the requested error tags:

- `E01`: basic fact error
- `E02`: carrying error
- `E03`: borrowing error
- `E04`: place-value alignment error
- `E05`: operation order error
- `E06`: decimal point or fraction unit error
- `E07`: copying or transcription error
- `E08`: omitted step
- `E11`: missing verification
