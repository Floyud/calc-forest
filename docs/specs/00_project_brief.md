# Project Brief

## Product Name

我的计算森林

## One-Line Positioning

面向小学数学教学场景的 Dify-first 教育智能体，帮助教师用结构化诊断、短时练习和教师审核工作流更快看清学生真实错因。

## Product Essence

- 教师工作台优先，先解决“看清错因、组织讲评、控制风险”。
- Dify 作为主交付入口，承载智能体交互、工作流编排与开发证据。
- 森林保留为品牌隐喻与成长语气，不作为当前 MVP 主叙事。

## Current Phase

Teacher-side MVP with Dify-first workflow direction.

The MVP is not a full student product, parent product, OCR product, full textbook graph, or complete long-term forest-growth product.

## Target Users

- Primary user: primary-school math teacher.
- Secondary user: student, only through teacher-reviewed practice and feedback.
- Non-MVP user: parent.

## Core Problem

Primary-school calculation errors are frequent, but teachers need more than right/wrong marking. They need to know:

- Which error types are common in class.
- Which students repeatedly show the same error.
- What should be reviewed tomorrow.
- How to keep practice short, targeted, and compliant with double-reduction expectations.

## MVP Promise

Given a synthetic or manually entered answer record, the system returns:

- Correctness.
- Main error tag.
- Evidence.
- Teacher action.
- Student-facing hint.
- `pending_teacher_review` status.

## Key Constraints

- Practice must be short: classroom 3-5 minutes, home practice vision <=5 minutes.
- Teacher workflow must be simple.
- Guidance must stay aligned with current textbook methods.
- Technology should adapt to children by grade, not ask children to adapt to complicated tooling.
- Forest language, if used, must stay non-ranking and non-pressure.
- AI output must be reviewed by teachers.
- Demo data must be synthetic or anonymized.
- Competition vision must not be represented as implemented MVP.
