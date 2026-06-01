# API 设计方案

> 最后更新：2026-05-19 | 基于代码库实际状态
> 
> 相关文档：`docs/engineering/architecture.md` · `docs/engineering/data_model.md` · `docs/specs/05_data_contract.md`

## 概览

FastAPI 后端提供 ~75 个 REST 端点，分布在 13 个路由器中。所有端点前缀 `/api`（除 `/health`）。

**运行环境：**
```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**OpenAPI 文档：** `http://127.0.0.1:8000/docs`

---

## 1. 系统配置 (`routers/config.py`)

| 方法 | 端点 | 功能 | 说明 |
|---|---|---|---|
| GET | `/health` | 健康检查 | 返回服务状态 |
| GET | `/api/tree-species` | 树种配置 | 8 种核心树种 |
| GET | `/api/encouragements` | 鼓励语配置 | 低压力成长语气 |
| GET | `/api/config/llm-status` | LLM 连接状态 | 检测 DeepSeek/GLM 可用性 |
| POST | `/api/config/llm-mode` | 切换 LLM 模式 | 官方/代理/智谱 |
| GET | `/api/config/dify-status` | Dify 连接状态 | 本地/云端/直连 |
| POST | `/api/tts/generate` | 语音合成 | Edge-TTS，返回音频 |
| GET | `/api/pdfs/{pdf_id}` | 获取 PDF | 下载生成的 PDF 文件 |
| POST | `/api/reports/{student_id}/generate` | 生成学生报告 | 个人学习报告 PDF |
| GET | `/api/reports/{student_id}` | 学生报告列表 | 历史报告 |
| POST | `/api/reports/class/{class_id}/generate` | 生成班级报告 | 班级整体分析 PDF |
| GET | `/api/reports/class/{class_id}` | 班级报告列表 | 历史班级报告 |

---

## 2. 认证 (`routers/auth.py`)

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/auth/login` | 教师登录（手机号 + 密码） |
| GET | `/api/auth/me` | 当前教师信息 |

---

## 3. 学生认证 (`routers/student_auth.py`)

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/student-auth/login` | 学生登录（学号 + 密码） |
| GET | `/api/student-auth/me` | 当前学生信息 |
| GET | `/api/student-auth/class-list/{class_id}` | 班级学生列表 |

---

## 4. 诊断 (`routers/diagnosis.py`)

核心诊断链路，6 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/diagnose` | 单题错因诊断（纯规则引擎） |
| POST | `/api/dify/chat` | Dify 聊天代理（透传） |
| POST | `/api/practice/recommend` | 按错因推荐练习 |
| POST | `/api/dify/session-draft` | 组合端点：诊断+练习+引导 → Dify payload |
| POST | `/api/dify/full-pipeline` | 全流程：诊断+画像更新+成长 |
| POST | `/api/dify/pipeline-stream` | SSE 流式管道（实时推送） |

### POST /api/diagnose

请求：
```json
{
  "record_id": "R0002",
  "student_id": "S001",
  "grade": 6,
  "class_id": "G6C1",
  "knowledge_point": "fraction_addition",
  "problem": "2/3 + 1/6",
  "correct_answer": "5/6",
  "student_answer": "3/9",
  "student_steps": ["通分", "2/3 = 4/6", "4/6 + 1/6 = 5/6"],
  "time_spent_seconds": 45,
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
    "code": "E-K05",
    "label": "通分错误",
    "confidence": 0.85,
    "evidence": "学生将分子分母分别相加，未正确通分",
    "teacher_action": "检查通分步骤：最小公倍数是否正确",
    "student_feedback": "想一想：2/3 和 1/6 的分母相同吗？"
  },
  "secondary_errors": [],
  "normalized": {
    "expected_value": "5/6",
    "student_value": "3/9"
  },
  "review_status": "pending_teacher_review"
}
```

---

## 5. 作业 (`routers/homework.py`)

作业全生命周期，16 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/homework/generate` | 生成作业（自适应难度 A/B/C） |
| GET | `/api/homework/{homework_id}` | 作业详情 |
| POST | `/api/homework/assign` | 布置作业 |
| POST | `/api/homework/submit` | 学生提交作业 |
| POST | `/api/homework/grade` | 批改作业（规则引擎） |
| POST | `/api/homework/{homework_id}/generate-pdf` | 生成作业 PDF |
| GET | `/api/homework/{homework_id}/pdfs` | 作业 PDF 列表 |
| POST | `/api/homework/batch-pipeline` | 批量流水线（诊断+统计） |
| POST | `/api/homework/batch-pipeline/class` | 班级批量流水线 |
| POST | `/api/homework/lifecycle` | 作业生命周期（全流程/单步） |
| POST | `/api/homework/{homework_id}/simulate` | 模拟学生作答（演示用） |
| POST | `/api/homework/{homework_id}/ai-grade` | AI 批改（LLM 增强） |
| POST | `/api/homework/{homework_id}/ai-profile` | AI 画像更新 |
| GET | `/api/homework/class/{class_id}/analytics` | 班级作业分析 |
| GET | `/api/homework/{homework_id}/analytics` | 单次作业分析 |
| GET | `/api/homework/student/{student_id}/summary` | 学生作业汇总 |
| POST | `/api/homework/{homework_id}/scan-grade` | 扫码批改（OCR） |

---

## 6. 学生管理 (`routers/student.py`)

教师端学生信息，10 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/students/{student_id}` | 学生基本信息 |
| GET | `/api/students/{student_id}/profile` | 学生画像 |
| PATCH | `/api/students/{student_id}/profile` | 更新学生画像 |
| GET | `/api/students/{student_id}/growth` | 成长数据 |
| POST | `/api/students/{student_id}/growth/record` | 记录练习天数 |
| GET | `/api/students/{student_id}/trajectory` | 错因轨迹 |
| GET | `/api/students/{student_id}/mastery` | 掌握度（BKT） |
| GET | `/api/students/{student_id}/ai-analysis` | AI 分析报告 |
| GET | `/api/students/{student_id}/homework-summary` | 作业汇总 |
| GET | `/api/guidance/context/{student_id}` | 引导上下文 |

---

## 7. 学生端 API (`routers/student_api.py`)

学生自主操作，10 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/students/{student_id}/dashboard` | 学生仪表盘 |
| GET | `/api/students/{student_id}/pending-homework` | 待做作业列表 |
| GET | `/api/students/{student_id}/homework/{homework_id}/problems` | 作业题目 |
| POST | `/api/students/{student_id}/practice/start` | 开始练习 |
| GET | `/api/students/{student_id}/practice/{session_id}/next` | 下一题 |
| POST | `/api/students/{student_id}/practice/{session_id}/answer` | 提交答案 |
| POST | `/api/students/{student_id}/practice/{session_id}/end` | 结束练习 |
| GET | `/api/students/{student_id}/homework/{homework_id}/pdf` | 下载作业 PDF |
| POST | `/api/students/{student_id}/homework/{homework_id}/scan-grade` | 扫码批改（501 未实现） |

---

## 8. 课堂测验 (`routers/quiz.py`)

课堂实时测验，6 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/quiz/generate` | 生成测验 |
| GET | `/api/quiz/{quiz_id}` | 测验详情 |
| POST | `/api/quiz/{quiz_id}/response` | 记录班级整体响应 |
| GET | `/api/quiz/{quiz_id}/summary` | 测验统计 |
| POST | `/api/quiz/{quiz_id}/student-answer` | 学生答题 |
| GET | `/api/quiz/{quiz_id}/live-stats` | 实时统计 |

---

## 9. 班级视图 (`routers/classroom.py`)

班级信息，5 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/classes/{class_id}` | 班级详情 |
| GET | `/api/classes/{class_id}/summary` | 班级摘要 |
| GET | `/api/classes/{class_id}/forest` | 森林视图 |
| GET | `/api/classes/{class_id}/homework-pdfs` | 班级作业 PDF |
| GET | `/api/classes/{class_id}/ai-portrait` | AI 班级画像 |

---

## 10. 知识库 (`routers/knowledge.py`)

知识检索与题库，6 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/knowledge/search` | FTS5 全文搜索 |
| GET | `/api/knowledge/points` | 知识点列表 |
| GET | `/api/knowledge/graph` | 知识图谱 |
| GET | `/api/problem-bank` | 题库查询 |
| GET | `/api/exercise-types` | 题型列表 |
| GET | `/api/exercise-types/{type_id}` | 题型详情 |

---

## 11. 教学体系 (`routers/curriculum.py`)

人教版课程体系，6 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/curriculum/units` | 教学单元列表 |
| GET | `/api/curriculum/schedule/{class_id}` | 班级课表 |
| PUT | `/api/curriculum/schedule/{class_id}` | 更新课表 |
| GET | `/api/curriculum/calendar` | 校历 |
| GET | `/api/cycles/current` | 当前学习周期 |
| GET | `/api/curriculum/week-calc` | 周次计算 |

---

## 12. OCR (`routers/ocr.py`)

作业拍照识别，4 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| POST | `/api/ocr/recognize` | 通用 OCR 识别 |
| POST | `/api/ocr/recognize-work` | 作业识别（结构化） |
| POST | `/api/ocr/upload` | 上传图片 |
| POST | `/api/ocr/baidu-correct` | 百度智能作业纠错 |

---

## 13. 课表 (`routers/timetable.py`)

课表管理 + 自动布置，6 个端点。

| 方法 | 端点 | 功能 |
|---|---|---|
| GET | `/api/timetable/{class_id}` | 课表查询 |
| PUT | `/api/timetable/{class_id}` | 更新课表 |
| GET | `/api/timetable/{class_id}/week-view` | 周视图 |
| GET | `/api/timetable/{class_id}/today` | 今日课程 |
| POST | `/api/timetable/{class_id}/auto-assign` | 自动布置作业 |
| POST | `/api/timetable/{class_id}/assign` | 手动布置作业 |

---

## 错因编码体系

API 使用的错因编码分两类：

- **知识类 (E-K)**: E-K01 ~ E-K23 — 知识理解不足导致的错误
- **习惯类 (E-H)**: E-H01 ~ E-H21 — 习惯性粗心导致的错误
- **未知**: E99 — 暂未识别的错因

唯一权威来源：`docs/specs/04_error_taxonomy.md` + `knowledge_base/01_error_taxonomy/`

---

## 通用约定

### 响应格式

所有端点返回 JSON。错误响应：
```json
{
  "detail": "错误描述"
}
```

### 审核状态

所有 AI 生成的内容带 `review_status` 字段：
- `"pending_teacher_review"` — 待教师审核（默认）
- `"approved"` — 教师已确认
- `"rejected"` — 教师已驳回

### 分页

列表端点支持 `offset` 和 `limit` 查询参数。

### 认证

教师端和学生端使用不同的认证机制。详见 `routers/auth.py` 和 `routers/student_auth.py`。
