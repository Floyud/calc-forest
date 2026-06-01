# 数据模型设计

> 最后更新：2026-05-19 | 基于代码库实际状态
>
> 相关文档：`docs/engineering/architecture.md` · `docs/engineering/api_plan.md` · `docs/specs/04_error_taxonomy.md`

## 概览

数据层由两部分组成：
1. **SQLite 数据库** — 33 张表 + 1 个 FTS5 虚拟表，定义在 `calc_forest/backend/app/db.py`
2. **Pydantic 模型** — 请求/响应 schema，定义在 `calc_forest/backend/app/schemas.py`

---

## 数据库表 (33 张)

### 基础实体 (4 张)

#### `students`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 学生编号，如 `S001` |
| name | TEXT | 学生姓名（合成） |
| grade | INTEGER | 年级 1-6 |
| class_id | TEXT FK | 班级编号 |
| guidance_mode | TEXT | 引导模式: standard/exploration/challenge |
| textbook_version | TEXT | 教材版本 |
| start_grade | INTEGER | 入学年级 |
| enrolled_at | TEXT | 入学时间 |
| personality_tags | TEXT | 性格标签 (JSON) |
| learning_style | TEXT | 学习风格 |
| notes | TEXT | 备注 |
| student_number | TEXT | 学号 |

#### `classes`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 班级编号，如 `G6C1` |
| name | TEXT | 班级名称 |
| grade | INTEGER | 年级 |
| academic_year | TEXT | 学年 |
| semester | TEXT | 学期 |
| student_ids | TEXT | 学生 ID 列表 (JSON) |
| teacher_id | TEXT FK | 教师 ID |

#### `teachers`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 教师 ID |
| name | TEXT | 教师姓名 |
| phone | TEXT | 手机号 |
| password_hash | TEXT | 密码哈希 |
| avatar | TEXT | 头像 URL |
| class_ids | TEXT | 负责班级 (JSON) |
| created_at | TEXT | 创建时间 |

#### `academic_cycles`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 周期 ID |
| cycle_type | TEXT | 周期类型 |
| academic_year | TEXT | 学年 |
| grade | INTEGER | 年级 |
| start_date | TEXT | 开始日期 |
| end_date | TEXT | 结束日期 |
| total_days | INTEGER | 总天数 |
| practice_goal_days | INTEGER | 练习目标天数 |
| available_tree_species | TEXT | 可选树种 (JSON) |

---

### 作业闭环 (7 张)

#### `homework`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 作业 ID |
| class_id | TEXT FK | 班级 |
| student_id | TEXT FK | 学生（可为空=班级作业） |
| cycle_id | TEXT FK | 学习周期 |
| grade | INTEGER | 年级 |
| knowledge_points | TEXT | 知识点列表 (JSON) |
| error_codes_target | TEXT | 目标错因 (JSON) |
| status | TEXT | 状态: draft/assigned/submitted/graded |
| assigned_date | TEXT | 布置日期 |
| due_date | TEXT | 截止日期 |
| generated_by | TEXT | 生成方式: rule/llm |
| created_at | TEXT | 创建时间 |

#### `homework_problems`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| homework_id | TEXT FK | 所属作业 |
| sequence | INTEGER | 题序 |
| problem | TEXT | 题目 |
| correct_answer | TEXT | 标准答案 |
| knowledge_point | TEXT | 知识点 |
| target_error_code | TEXT | 目标错因 |
| difficulty | TEXT | 难度: A/B/C |

#### `homework_submissions`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| homework_id | TEXT FK | 作业 |
| student_id | TEXT FK | 学生 |
| submitted_at | TEXT | 提交时间 |
| status | TEXT | pending/submitted/graded |

#### `student_answers`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| submission_id | TEXT FK | 提交 |
| homework_id | TEXT FK | 作业 |
| student_id | TEXT FK | 学生 |
| problem_sequence | INTEGER | 题序 |
| problem | TEXT | 题目 |
| correct_answer | TEXT | 标准答案 |
| student_answer | TEXT | 学生答案 |
| student_steps | TEXT | 解题步骤 |
| is_correct | BOOLEAN | 是否正确 |
| error_code | TEXT | 错因编码 |
| error_label | TEXT | 错因标签 |
| confidence | REAL | 置信度 |
| evidence | TEXT | 诊断证据 |
| teacher_action | TEXT | 教师建议 |
| student_feedback | TEXT | 学生反馈 |
| created_at | TEXT | 创建时间 |

#### `homework_pdfs`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| homework_id | TEXT FK | 作业 |
| class_id | TEXT FK | 班级 |
| student_id | TEXT FK | 学生（可为空） |
| pdf_path | TEXT | PDF 文件路径 |
| pdf_type | TEXT | 类型: assignment/answer_sheet |
| generated_at | TEXT | 生成时间 |

#### `scanned_submissions`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| homework_id | TEXT FK | 作业 |
| pdf_path | TEXT | 扫描件路径 |
| ocr_status | TEXT | OCR 状态 |
| ocr_result_json | TEXT | OCR 结果 (JSON) |
| graded_status | TEXT | 批改状态 |
| uploaded_at | TEXT | 上传时间 |
| reviewed_at | TEXT | 审核时间 |

#### `grading_comments`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| homework_id | TEXT FK | 作业 |
| student_id | TEXT FK | 学生 |
| problem_sequence | INTEGER | 题序 |
| ai_comment | TEXT | AI 生成评语 |
| error_code | TEXT | 错因编码 |
| confidence | REAL | 置信度 |
| created_at | TEXT | 创建时间 |

---

### 诊断与错因 (3 张)

#### `diagnosis_history`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| class_id | TEXT FK | 班级 |
| grade | INTEGER | 年级 |
| problem | TEXT | 题目 |
| correct_answer | TEXT | 标准答案 |
| student_answer | TEXT | 学生答案 |
| student_steps | TEXT | 解题步骤 |
| is_correct | BOOLEAN | 是否正确 |
| error_code | TEXT | 错因编码 |
| error_label | TEXT | 错因标签 |
| confidence | REAL | 置信度 |
| evidence | TEXT | 诊断证据 |
| teacher_action | TEXT | 教师建议 |
| student_feedback | TEXT | 学生反馈 |
| teacher_summary | TEXT | 教师摘要 |
| guidance_mode | TEXT | 引导模式 |
| review_status | TEXT | 审核状态 |
| created_at | TEXT | 创建时间 |

#### `student_error_stats`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| error_code | TEXT | 错因编码 |
| total_attempts | INTEGER | 总尝试次数 |
| correct_count | INTEGER | 正确次数 |
| last_seen_at | TEXT | 最后出现时间 |

#### `student_error_trajectory`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| unit_id | TEXT FK | 教学单元 |
| week_number | INTEGER | 周次 |
| error_code | TEXT | 错因编码 |
| error_count | INTEGER | 错误次数 |
| correct_count | INTEGER | 正确次数 |
| accuracy | REAL | 正确率 |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |

---

### 课堂测验 (4 张)

#### `quiz_sessions`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 测验 ID |
| class_id | TEXT FK | 班级 |
| title | TEXT | 测验标题 |
| status | TEXT | 状态 |
| target_error_codes | TEXT | 目标错因 (JSON) |
| problem_count | INTEGER | 题数 |
| difficulty | TEXT | 难度 |
| grade | INTEGER | 年级 |
| created_at | TEXT | 创建时间 |
| completed_at | TEXT | 完成时间 |

#### `quiz_problems`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| quiz_id | TEXT FK | 测验 |
| sequence | INTEGER | 题序 |
| problem | TEXT | 题目 |
| correct_answer | TEXT | 标准答案 |
| target_error_code | TEXT | 目标错因 |
| difficulty | TEXT | 难度 |
| knowledge_point | TEXT | 知识点 |
| hint | TEXT | 提示 |

#### `quiz_responses`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| quiz_id | TEXT FK | 测验 |
| problem_sequence | INTEGER | 题序 |
| class_response | TEXT | 班级整体响应 |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |

#### `quiz_student_answers`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| quiz_id | TEXT FK | 测验 |
| student_id | TEXT FK | 学生 |
| problem_sequence | INTEGER | 题序 |
| student_answer | TEXT | 学生答案 |
| is_correct | BOOLEAN | 是否正确 |
| answered_at | TEXT | 答题时间 |

---

### 学生成长 (4 张)

#### `student_cycle_progress`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| cycle_id | TEXT FK | 学习周期 |
| tree_species_id | TEXT | 树种 ID |
| days_completed | INTEGER | 已完成天数 |
| current_stage | TEXT | 当前阶段 |
| last_practice_date | TEXT | 最后练习日期 |

#### `practice_weeks`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| cycle_id | TEXT FK | 学习周期 |
| week_number | INTEGER | 周次 |
| start_date | TEXT | 开始日期 |
| end_date | TEXT | 结束日期 |
| label | TEXT | 标签 |

#### `student_practice_sessions`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| error_codes | TEXT | 目标错因 (JSON) |
| difficulty | TEXT | 难度 |
| started_at | TEXT | 开始时间 |
| ended_at | TEXT | 结束时间 |
| problems_done | INTEGER | 已做题数 |
| correct_count | INTEGER | 正确数 |
| status | TEXT | 状态: active/completed |

#### `student_practice_problems`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| session_id | TEXT FK | 练习会话 |
| sequence | INTEGER | 题序 |
| problem | TEXT | 题目 |
| correct_answer | TEXT | 标准答案 |
| target_error_code | TEXT | 目标错因 |
| difficulty | TEXT | 难度 |
| student_answer | TEXT | 学生答案 |
| is_correct | BOOLEAN | 是否正确 |
| error_code | TEXT | 实际错因 |
| answered_at | TEXT | 答题时间 |

---

### 教学体系 (3 张)

#### `teaching_units`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| grade | INTEGER | 年级 |
| semester | TEXT | 学期 |
| unit_number | INTEGER | 单元号 |
| title | TEXT | 单元标题 |
| domain | TEXT | 知识领域 |
| hours_planned | INTEGER | 计划课时 |
| sort_order | INTEGER | 排序 |
| parent_id | TEXT FK | 父单元 |
| textbook_version | TEXT | 教材版本 |

#### `teaching_schedule`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| class_id | TEXT FK | 班级 |
| week_number | INTEGER | 周次 |
| unit_id | TEXT FK | 教学单元 |
| start_date | TEXT | 开始日期 |
| end_date | TEXT | 结束日期 |
| status | TEXT | 状态 |
| notes | TEXT | 备注 |
| is_custom | BOOLEAN | 是否自定义 |

#### `calendar_weeks`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| academic_year | TEXT | 学年 |
| semester | TEXT | 学期 |
| week_number | INTEGER | 周次 |
| start_date | TEXT | 开始日期 |
| end_date | TEXT | 结束日期 |
| is_holiday | BOOLEAN | 是否假期 |
| label | TEXT | 标签 |

---

### 知识库 (4 张 + 1 FTS5)

#### `knowledge_points`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| error_code | TEXT | 关联错因编码 |
| topic | TEXT | 知识点主题 |
| description | TEXT | 描述 |
| method | TEXT | 解题方法 |
| example | TEXT | 示例 |
| prerequisite_ids | TEXT | 前置知识点 (JSON) |
| difficulty_level | TEXT | 难度等级 |
| unit_number | INTEGER | 教学单元 |
| sort_order | INTEGER | 排序 |

#### `concept_relations`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| source_id | TEXT FK | 源知识点 |
| target_id | TEXT FK | 目标知识点 |
| relation_type | TEXT | 关系类型 |
| weight | REAL | 权重 |

#### `problem_bank`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| problem_text | TEXT | 题目（含格式） |
| problem_plain | TEXT | 题目（纯文本） |
| correct_answer | TEXT | 标准答案 |
| error_code | TEXT | 关联错因 |
| knowledge_point | TEXT | 知识点 |
| difficulty | TEXT | 难度 |
| method | TEXT | 解题方法 |
| source | TEXT | 来源 |
| use_count | INTEGER | 使用次数 |
| verified | BOOLEAN | 是否验证 |
| created_at | TEXT | 创建时间 |

#### `week_calc_mapping`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| week_start | TEXT | 周开始 |
| week_end | TEXT | 周结束 |
| calc_type | TEXT | 计算类型 |
| calc_subtypes | TEXT | 计算子类型 (JSON) |
| error_codes | TEXT | 关联错因 (JSON) |
| is_review | BOOLEAN | 是否复习 |
| review_types | TEXT | 复习类型 (JSON) |
| semester | TEXT | 学期 |
| grade | INTEGER | 年级 |

#### `knowledge_points_fts` (FTS5 虚拟表)

全文搜索索引，覆盖 knowledge_points 的 topic, description, method, example 字段。

---

### 画像与报告 (2 张)

#### `profile_snapshots`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| student_id | TEXT FK | 学生 |
| snapshot_type | TEXT | 快照类型 |
| analysis_json | TEXT | 分析结果 (JSON) |
| portrait_summary | TEXT | 画像摘要 |
| personality_tags | TEXT | 性格标签 |
| growth_narrative | TEXT | 成长叙述 |
| created_at | TEXT | 创建时间 |

#### `exercise_types`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| parent_id | TEXT FK | 父题型 |
| category | TEXT | 分类 |
| name | TEXT | 题型名称 |
| code | TEXT | 题型编码 |
| difficulty_range | TEXT | 难度范围 |
| related_error_codes | TEXT | 关联错因 (JSON) |
| knowledge_points | TEXT | 关联知识点 (JSON) |
| description | TEXT | 描述 |
| example_problem | TEXT | 示例题目 |
| example_answer | TEXT | 示例答案 |
| sort_order | INTEGER | 排序 |
| is_active | BOOLEAN | 是否启用 |
| grade_range | TEXT | 年级范围 |
| textbook_unit | TEXT | 教材单元 |

---

### 其他 (1 张)

#### `error_code_knowledge_map`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | |
| error_code | TEXT | 错因编码 |
| unit_id | TEXT FK | 教学单元 |
| unit_title | TEXT | 单元标题 |
| knowledge_point | TEXT | 知识点 |
| typical_error | TEXT | 典型错误 |
| sort_order | INTEGER | 排序 |

---

## Pydantic 模型 (`schemas.py`)

### 诊断相关

| 模型 | 用途 |
|---|---|
| `DiagnosisRequest` | POST /api/diagnose 请求体 |
| `DiagnosisResponse` | 诊断响应（含错因、证据、审核状态） |
| `ErrorTag` | 错因标签（code + label + confidence + evidence） |

### 作业相关

| 模型 | 用途 |
|---|---|
| `HomeworkGenerateRequest` | 生成作业请求 |
| `HomeworkAssignRequest` | 布置作业请求 |
| `HomeworkSubmitRequest` | 提交作业请求 |
| `HomeworkGradeRequest` | 批改请求 |

### 成长相关

| 模型 | 用途 |
|---|---|
| `TreeSpecies` | 树种配置 |
| `EncouragementRule` | 鼓励语规则 |
| `GrowthMilestone` | 成长里程碑 |
| `GuidanceMode` | 引导模式枚举 |

### Dify 集成

| 模型 | 用途 |
|---|---|
| `DifySessionDraftRequest` | 会话草稿请求 |
| `DifySessionDraftResponse` | 会话草稿响应 |
| `StudentGuidance` | 学生引导数据 |

### 练习相关

| 模型 | 用途 |
|---|---|
| `PracticeRecommendationRequest` | 练习推荐请求 |
| `PracticeRecommendationResponse` | 练习推荐响应 |

---

## 错因编码体系

> 唯一权威来源：`docs/specs/04_error_taxonomy.md` + `knowledge_base/01_error_taxonomy/`

- **知识类 (E-K)**: E-K01 ~ E-K23 — 知识理解不足
- **习惯类 (E-H)**: E-H01 ~ E-H21 — 习惯性粗心
- **未知**: E99 — 暂未识别

---

## 数据文件

```text
calc_forest/backend/data/
├── app.db                    # SQLite 数据库
├── demo_answer_records.json  # 演示数据（24 条合成记录）
├── tree_species.json         # 树种配置
└── encouragements.json       # 鼓励语配置
```

所有数据均为合成数据，不包含真实学生信息。
