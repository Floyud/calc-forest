# 学生画像 Schema

## 设计目标

学生画像不是评价学生好坏，而是服务精准教学。首版画像只保留与计算学习相关的最小数据。

## StudentProfile

```json
{
  "student_id": "S001",
  "grade": 4,
  "class_id": "G4C2",
  "knowledge_mastery": {
    "integer_add_sub": 0.72,
    "integer_mul_div": 0.66,
    "decimal_calculation": 0.48
  },
  "error_tag_counts": {
    "E02": 5,
    "E03": 8,
    "E11": 3
  },
  "recent_trend": {
    "window_days": 14,
    "accuracy": 0.71,
    "dominant_error_tags": ["E03", "E11"]
  },
  "correction_effect": {
    "corrected_count": 12,
    "repeat_error_rate": 0.25
  },
  "recommended_level": "A",
  "teacher_notes": "退位减法反复出错，订正后同类题有改善。"
}
```

## 字段说明

| 字段 | 含义 | 首版来源 |
| --- | --- | --- |
| `student_id` | 脱敏学生编号 | 教师手工维护 |
| `grade` | 年级 | 教师手工维护 |
| `class_id` | 班级编号 | 教师手工维护 |
| `knowledge_mastery` | 知识点掌握度 | 作答记录聚合 |
| `error_tag_counts` | 错因频次 | 诊断结果累加 |
| `recent_trend` | 近期表现 | 最近 N 条记录统计 |
| `correction_effect` | 订正效果 | 订正记录统计 |
| `recommended_level` | 推荐练习层级 | 规则生成 |
| `teacher_notes` | 教师备注 | 教师可选填写 |

## 分层规则草案

- **A 层补救**：近期准确率低于 70%，且同一错因重复出现 3 次以上。
- **B 层巩固**：近期准确率 70%-90%，存在不稳定错因。
- **C 层提升**：近期准确率高于 90%，基础错因少，可做变式和综合题。

分层结果只作为建议，不自动决定学生水平。

## 隐私原则

- 使用 `student_id`，不在系统内默认保存真实姓名。
- 演示数据只使用合成学生编号。
- LLM 调用只传递脱敏后的题目、答案、标签和统计摘要。
- 教师导出的报告不包含不必要的个人信息。
