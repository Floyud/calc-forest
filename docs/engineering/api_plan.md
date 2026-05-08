# API 设计方案

## 当前实现口径

本页默认记录**比赛与 Dify 教师主链路直接相关**的接口子集，不等于整个后端的完整 inventory。当前比赛叙事优先围绕教师工作台、错因诊断闭环、短时反馈与教师审核边界组织；更完整的学生、班级、作业、测验接口已在代码中存在，但不全部展开到此文档。

当前 MVP 现已实现以下接口：

| 接口 | 方法 | 作用 |
| --- | --- | --- |
| `/health` | GET | 健康检查 |
| `/api/diagnose` | POST | 对一条学生作答进行错因诊断 |
| `/api/practice/recommend` | POST | 根据错因和引导模式返回短时巩固练习 |
| `/api/tree-species` | GET | 返回成长语气层可选树种配置 |
| `/api/encouragements` | GET | 返回可选鼓励语配置 |
| `/api/dify/session-draft` | POST | 为 Dify 夜间版工作流返回完整诊断草案 |

完整题目解析、学生答案分析、教学策略、批量评测、会话导出等能力仍是后续扩展，不作为当前实现承诺。

## 运行环境

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## `GET /health`

响应：

```json
{
  "ok": true,
  "service": "primary-math-diagnosis-agent",
  "version": "0.1.0"
}
```

## `POST /api/diagnose`

请求：

```json
{
  "record_id": "R0002",
  "student_id": "S001",
  "grade": 4,
  "class_id": "G4C2",
  "knowledge_point": "continuous_borrowing_subtraction",
  "problem": "604 - 278",
  "correct_answer": "326",
  "student_answer": "436",
  "student_steps": [
    "4 cannot subtract 8, borrow from tens",
    "10 - 7 = 3",
    "6 - 2 = 4"
  ],
  "time_spent_seconds": 75,
  "source": "manual"
}
```

响应：

```json
{
  "record_id": "R0002",
  "student_id": "S001",
  "is_correct": false,
  "primary_error": {
    "code": "E03",
    "label": "退位错误",
    "confidence": 0.74,
    "evidence": "604-278 存在需要退位的数位，学生结果与标准答案偏差较大。",
    "teacher_action": "检查每个不够减的位置是否完成退位和被借位减一。",
    "student_feedback": "逐位检查：哪一位不够减？借位后前一位有没有少 1？"
  },
  "secondary_errors": [],
  "normalized": {
    "expected_value": "326",
    "student_value": "436",
    "left_to_right_value": null
  },
  "teacher_summary": "S001 本题错误。主要判断：退位错误。证据：604-278 存在需要退位的数位，学生结果与标准答案偏差较大。",
  "guidance_mode": "standard",
  "growth_milestone": null,
  "review_status": "pending_teacher_review"
}
```

## 错因编码

当前 API 使用 `E01-E11`，以 `docs/specs/04_error_taxonomy.md` 为准。`E99` 表示暂未识别错因。

## `POST /api/practice/recommend`

请求：

```json
{
  "error_code": "E03",
  "grade": 4,
  "guidance_mode": "standard"
}
```

响应要点：

- 返回 2 到 3 道短时巩固题。
- 标注 `guidance_mode`，区分标准/探索/挑战。
- `estimated_minutes` 保持短时练习口径。

## `GET /api/tree-species`

返回当前 8 种核心树种配置，用于品牌表达或可选成长语气配置。

## `GET /api/encouragements`

返回鼓励语配置，当前采用低压力、教师可控的成长语气口径。

## `POST /api/dify/session-draft`

这是当前 Dify 版工作流的组合接口。它接收题目、标准答案、学生作答、引导模式和可选树种字段，直接返回：

- 结构化诊断结果
- 短时练习推荐
- 教师摘要
- 学生引导草案
- 可选树种信息
- 可选鼓励语

用途：在没有额外模型配置的情况下，也能让 Dify 先跑通首个完整教师侧闭环。当前主证明点仍是教师诊断、审核与短时反馈，而非成长语气字段本身。

## Dify / Coze 调用建议

Dify 或 Coze 至少需要配置以下 HTTP Tools：

```http
POST /api/diagnose
POST /api/practice/recommend
GET /api/tree-species
GET /api/encouragements
POST /api/dify/session-draft
```

工作流负责收集教师输入、调用接口、把结构化响应整理成教师可读摘要。LLM 不应改写 `primary_error.code`。

## 后续扩展

后续可以拆出题目解析、答案步骤抽取、教学策略和批量评测接口，但需要先在 `docs/specs/05_data_contract.md` 更新产品契约，再实现代码。
