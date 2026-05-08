# User Flows

## Teacher Quick Flow

```text
Teacher enters a short calculation record
  -> Dify workflow calls diagnosis and practice tools
  -> system returns pending-review diagnosis, evidence, and practice draft
  -> teacher reviews, edits, and decides what can be used in class or home practice
```

Teacher-side expectation:

- Step 1: 录入题目、答案、学生作答。
- Step 2: 查看 AI 给出的错因、证据、引导和练习草案。
- Step 3: 审核后用于讲评、订正或短时巩固。

## Future Classroom Flow

```text
Teacher sets teaching progress
  -> system keeps content aligned to the current textbook method
  -> system generates 3-5 minute practice
  -> students answer
  -> teacher sees class accuracy, top errors, and students needing attention
  -> teacher adjusts next lesson
```

## Future Home Flow

```text
Teacher-approved weak points
  -> student sees <=5 minute practice
  -> student answers through grade-appropriate input
  -> student receives gentle textbook-aligned guidance
  -> student may receive gentle growth-tone feedback without ranking pressure
  -> data returns to teacher dashboard
```

## Future Forest Motivation Flow

```text
student chooses a tree species
  -> each semester or holiday grows one tree
  -> practice accumulates visible growth stages
  -> forest keeps the child's own long-term record
  -> no comparison leaderboard is introduced
```

Status: vision layer only. This is not the current teacher-side MVP center.

## Future Holiday Flow

```text
holiday starts
  -> tree enters rest/dormant state
  -> no push, no ranking, no forced streak
  -> student may voluntarily review learned content
  -> content never jumps ahead of current progress
  -> holiday data does not create class pressure
```

## MVP Boundary

Only the teacher diagnosis flow and teacher workbench-oriented review loop are implemented now. Other flows are product vision, tone layer, or competition narrative until explicitly built.
