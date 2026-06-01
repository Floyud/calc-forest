# Data Contract

> 最后更新：2026-05-19
>
> 相关文档：`docs/engineering/api_plan.md`（完整端点清单） · `docs/engineering/data_model.md`（数据模型）

## Primary Endpoint

`POST /api/diagnose`

当前已实现 ~75 个端点，完整清单见 `docs/engineering/api_plan.md`。

## Current Supporting Tool Endpoints

- `POST /api/practice/recommend`
- `GET /api/tree-species`
- `GET /api/encouragements`
- `POST /api/dify/session-draft`

These supporting endpoints are intended for the Dify-first teacher workbench workflow. `POST /api/diagnose` remains the core diagnosis contract, while tree/encouragement endpoints are optional tone-layer support rather than the MVP center.

## Request

```json
{
  "record_id": "R0001",
  "student_id": "S001",
  "grade": 4,
  "class_id": "G4C2",
  "knowledge_point": "continuous_borrowing_subtraction",
  "problem": "402-178=",
  "correct_answer": "224",
  "student_answer": "334",
  "student_steps": [],
  "time_spent_seconds": 60,
  "source": "manual"
}
```

## Response

```json
{
  "record_id": "R0001",
  "student_id": "S001",
  "is_correct": false,
  "primary_error": {
    "code": "E03",
    "label": "退位错误",
    "confidence": 0.74,
    "evidence": "402-178 存在需要退位的数位，学生结果与标准答案偏差较大。",
    "teacher_action": "检查每个不够减的位置是否完成退位和被借位减一。",
    "student_feedback": "逐位检查：哪一位不够减？借位后前一位有没有少 1？"
  },
  "secondary_errors": [],
  "normalized": {
    "expected_value": "224",
    "student_value": "334",
    "left_to_right_value": null
  },
  "teacher_summary": "S001 本题错误。主要判断：退位错误。证据：...",
  "guidance_mode": "standard",
  "growth_milestone": null,
  "review_status": "pending_teacher_review"
}
```

## Status Rules

- `review_status` defaults to `pending_teacher_review`.
- No AI-generated diagnosis or practice should be treated as student-visible until reviewed.
- Demo data must be synthetic or anonymized.

## Demo Data

Path:

```text
calc_forest/backend/data/demo_answer_records.json
```

Required fields:

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
