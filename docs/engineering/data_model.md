# 数据模型设计

## 当前实现模型

当前 MVP 使用 Pydantic 模型承载请求与响应，代码在 `development/app/schemas.py`。

## AnswerRecord / DiagnosisRequest

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `record_id` | string/null | 合成作答记录 ID |
| `student_id` | string | 匿名学生编号，如 `S001` |
| `grade` | int | 年级，1-6 |
| `class_id` | string/null | 匿名班级编号 |
| `knowledge_point` | string/null | 知识点标识 |
| `problem` | string | 题目文本 |
| `correct_answer` | string | 标准答案 |
| `student_answer` | string | 学生答案 |
| `student_steps` | string[] | 可选步骤 |
| `time_spent_seconds` | int/null | 用时 |
| `source` | string | 来源，如 `manual` |

## ErrorTag

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | enum | `E01-E11` 或 `E99` |
| `label` | string | 中文错因名称 |
| `confidence` | float | 0-1 |
| `evidence` | string | 诊断证据 |
| `teacher_action` | string | 教师处理建议 |
| `student_feedback` | string | 学生可读提示 |

## DiagnosisResponse

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `record_id` | string/null | 作答记录 ID |
| `student_id` | string | 匿名学生编号 |
| `is_correct` | bool | 是否正确 |
| `primary_error` | ErrorTag | 主错因 |
| `secondary_errors` | ErrorTag[] | 次要错因 |
| `normalized` | object | 标准值、学生值、辅助计算值 |
| `teacher_summary` | string | 教师可读摘要 |
| `guidance_mode` | enum | `standard/exploration/challenge` |
| `growth_milestone` | object/null | 当前成长周期占位结构 |
| `review_status` | string | 默认 `pending_teacher_review` |

## Growth / Product Models

当前代码已加入以下基础模型，服务当前 Dify 教师工作流，并为品牌语气层与后续扩展保留接口：

- `GuidanceMode`
- `GrowthMilestone`
- `TreeSpecies`
- `EncouragementRule`
- `PracticeRecommendationRequest`
- `PracticeRecommendationResponse`
- `DifySessionDraftRequest`
- `DifySessionDraftResponse`
- `StudentGuidance`

## 错因 Taxonomy

PM-facing source of truth: `docs/specs/04_error_taxonomy.md`.

首版规则优先覆盖：

- `E01` 基础事实错误
- `E02` 进位错误
- `E03` 退位错误
- `E04` 数位对齐错误
- `E05` 运算顺序错误
- `E07` 抄题/转写错误
- `E08` 步骤遗漏
- `E11` 未验算

`E06` 小数点/分数单位错误有部分规则支持；`E09/E10` 暂不作为首版必测。

## Demo Data

Current file:

```text
development/data/demo_answer_records.json
```

The dataset contains 24 synthetic records. It must not contain real student names or sensitive information.

Additional config files:

```text
development/data/tree_species.json
development/data/encouragements.json
```

These config files are currently optional tone-layer support. They should not be interpreted as proof that long-term forest accumulation is already a delivered MVP feature.
