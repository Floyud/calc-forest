# 系统架构

## 总体原则

系统采用 **智能体平台编排 + 自研数学诊断服务 + 结构化数据层**。Dify/Coze 负责交互和工作流，FastAPI 负责核心业务能力。

```text
教师端 Web / Dify Agent / Coze Agent
  |
  v
Agent 工作流层
  |
  |-- RAG: 课程标准、错因标签、作业原则
  |-- LLM: 摘要、解释、讲评建议
  |-- HTTP Tool: 调用自研 API
  v
FastAPI 数学诊断服务
  |
  |-- 诊断规则引擎
  |-- 学生画像服务
  |-- 分层练习推荐
  |-- 班级统计服务
  |-- 题目模板与答案校验
  v
SQLite/PostgreSQL + 文件存储
```

## 技术栈

| 层级 | 首版选择 | 说明 |
| --- | --- | --- |
| Python 环境 | `/home/lyzhang/miniconda3/envs/pyt0` | 所有 Python 命令优先使用该环境 |
| 后端 | FastAPI + Pydantic | 适合快速做 AI 工具 API |
| 数据库 | SQLite 起步，PostgreSQL 备选 | 首版用 SQLite 便于演示和复现 |
| Agent 平台 | Dify-first | 负责 workflow、RAG、LLM、工具调用 |
| 展示入口 | Coze-ready | 第二阶段可作为教师端智能体入口 |
| 数学校验 | 规则引擎 + SymPy | 避免 LLM 直接决定对错 |
| OCR | 暂不阻塞，后续 PaddleOCR/Pix2Text | 首版支持手工录入和人工校正 |
| 前端 | React/Vue + ECharts 备选 | 首版文档先设计，工程后续搭建 |

## 数据流

1. 教师提交学生作答记录。
2. Agent 工作流检查字段并提示脱敏。
3. Agent 调用 `/api/diagnose`。
4. FastAPI 运行规则诊断，输出结构化错因。
5. LLM 把结构化结果整理成教师可读摘要，但不改写错因编码。
6. 教师审核后再用于学生练习或课堂讲评。
7. 学生画像、分层练习、班级摘要接口为下一阶段扩展。

## 核心模块

### 诊断规则引擎

负责判断常见计算错因：

- 基础事实错误。
- 进位/退位错误。
- 数位对齐错误。
- 运算顺序错误。
- 小数点/分数单位错误。
- 抄题/转写错误。
- 步骤遗漏。
- 未验算。

规则输出必须包含证据，不能只给标签。

### 学生画像服务

聚合学生作答记录：

- 知识点掌握度。
- 错因频次。
- 近期趋势。
- 订正效果。
- 推荐练习层级。

### 分层练习服务

用题库模板生成练习：

- A 层：基础补救。
- B 层：标准巩固。
- C 层：拓展变式。

每道题绑定知识点、错因、标准答案和推荐理由。

### Agent 工作流层

Dify 工作流负责：

- 收集教师输入。
- 调用自研 API。
- 查询知识库。
- 生成教师摘要。
- 标记审核状态。

LLM 不直接改写 API 返回的结构化诊断。

## 部署形态

首版本地演示：

```text
Dify 本地/云端工作流
FastAPI: http://localhost:8000
SQLite: ./development/data/app.db
演示数据: ./development/data/demo_answer_records.json
```

后续学校部署：

```text
内网 Web 服务
PostgreSQL
MinIO 图片存储
国产大模型 API
本地 OCR 或国内 OCR 服务
```

## 合规设计

- 学生使用编号，不默认存真实姓名。
- 原始图片不在首版采集。
- LLM 只接收脱敏作答文本和统计摘要。
- AI 生成练习和讲评建议都默认待教师审核。
- 学生端只展示教师确认后的反馈。
- 演示数据全部合成。

## 当前工程骨架

```text
development/app/
  main.py
  schemas.py
  services/
    diagnosis.py
    profiles.py
    practice.py
    summaries.py
development/data/
  demo_answer_records.json
development/tests/
  test_diagnosis.py
```

当前已实现 `GET /health` 和 `POST /api/diagnose`，画像、练习推荐和班级摘要服务仍是占位/后续扩展。
