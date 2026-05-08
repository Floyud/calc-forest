# PRD

## Background

The teacher-authored "我的计算森林"（原名"计算小树苗"）material highlights a real classroom need: calculation practice must follow the current teaching progress, stay short, and produce actionable diagnosis for teachers. The tree-growth metaphor, holiday mode, and home practice are valuable product vision, but the first version must prove the teacher-side diagnosis loop.

## Goals

- Help teachers identify calculation error causes instead of only marking answers wrong.
- Keep diagnosis explainable and teacher-reviewable.
- Build a Dify-first teacher workbench on top of a small, testable backend.
- Preserve the "森林" concept as a gentle brand and tone layer, without making long-term tree accumulation the current MVP center.
- Preserve the sense that this is a teacher-guided learning companion, not only a one-shot correction tool.

## Non-Goals

- No full textbook graph in MVP.
- No complete student app or parent app.
- No real student data.
- No OCR as a required dependency.
- No forced streaks, ranking, or holiday pressure.
- No promise that AI can identify every error with 100% accuracy.

## Core User Stories

1. As a teacher, I can submit a calculation problem, correct answer, student answer, and optional steps, then receive an error diagnosis with evidence.
2. As a teacher, I can see that the diagnosis is marked as pending review before being used with students.
3. As a teacher, I can use error tags to prepare short targeted practice.
4. As a student, I receive a guided four-step hint (comfort → reasoning → summary → practice) after teacher review, not a direct answer dump.
5. As a teacher, I can use a workbench-style flow to review diagnosis, guidance, and short practice before using them in class.
6. As a student at different levels, I receive guidance matched to my ability (standard/exploration/challenge).

## Product Principles From Teacher Feedback

- Follow teaching progress and textbook methods.
- Practice is short and precise (≤5 min/day).
- Growth matters more than score comparison — forest has no "standard size".
- Holiday mode is voluntary and low-disturbance.
- Teacher setup should be close to three steps.
- Student operation should be simple enough to learn quickly.
- "无论从几年级开始，今天就是最好的开始" — every starting grade is valid.
- Error guidance walks the child through thinking, never dumps the answer.
- Tree-species choice should carry ownership, curiosity, and light cross-disciplinary value.
- Technology should adapt to the child by grade, especially for lower-grade input burden.

## MVP Experience

Teacher-side flow:

```text
enter answer record -> Dify/teacher workbench -> diagnosis API -> structured result -> teacher reviews -> practice/brief can be prepared
```

Student-facing feedback is only represented as a reviewed draft in MVP. It is not directly published.
