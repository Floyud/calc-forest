# Teacher Feedback Digest

Sources:

```text
docs/source_materials/teacher_feedback/计算小树苗设计资料.docx
docs/source_materials/teacher_feedback/第4次修改（5月2号）.docx
docs/source_materials/teacher_feedback/计算练习出题原则和具体措施.docx
docs/source_materials/teacher_feedback/2025春学期教学进度计划.docx
docs/source_materials/teacher_feedback/人教版六年级上册数学整理资料.docx
```

This digest extracts product constraints from the teacher-authored material. It does not convert every idea into MVP commitment.

For the refreshed high-fidelity PDF exports, per-source curated notes, and the new master digest, see:

- `docs/research/teacher_feedback_curated/teacher_feedback_master_digest.md`
- `docs/research/teacher_feedback_curated/by_source/`

Forest-growth, long-term accumulation, and slogan-style phrases quoted below should be read as upstream teacher-source signals or brand/vision input, not as the current competition-facing delivery promise.

## Most Valuable Signals

1. **Follow teaching progress**
   - The system must avoid giving students content they have not learned.
   - The future product should support textbook version, grade, unit, and knowledge point.

2. **Keep practice short**
   - Classroom practice: 3-5 minutes.
   - Home practice vision: <=5 minutes.
   - Holiday review vision: 5-8 minutes, <=10 minutes.

3. **Teacher needs class diagnosis**
   - Correct-rate distribution.
   - High-frequency wrong questions.
   - Error categories.
   - Progress achievement.
   - Students needing attention.

4. **Low operation burden**
   - Teacher should be close to 3 steps.
   - Student should learn quickly.
   - Parent should not need to tutor.

5. **No added pressure**
   - No class ranking.
   - No forced holiday practice.
   - No holiday push notifications.
   - No compulsory streaks.

6. **Forest is the long-term metaphor, not only one tree**
   - Each semester or holiday can grow one tree.
   - Across grades 1-6, the child can accumulate a whole forest.
   - There is no "standard" forest size; late starters still have meaningful growth.

7. **Tree selection has educational value**
   - Students should be able to choose tree species they like.
   - Species variety can support nature knowledge, culture, and aesthetic interest.
   - MVP should keep species data lightweight; full 30+ knowledge cards remain later scope.

8. **Guidance should teach thinking, not dump answers**
   - Wrong answers should trigger a slow guided process.
   - Guidance must align with current textbook teaching methods.
   - Stronger students may optionally see extension methods after the textbook method is secure.

9. **Input needs to match children's developmental differences**
   - Lower grades benefit from voice-friendly or simple input.
   - Higher grades can use direct keyboard entry.
   - Photo upload is attractive, but should stay a future capability instead of blocking MVP.

10. **Practice generation must follow teaching progress**
   - “学什么，练什么；没新计算，就滚旧计算；只练计算，不出其他题型” is an explicit upstream rule.
   - Practice should remain short, progress-aligned, and calculation-only by default.

11. **Rolling review and wrong-question replay matter**
   - Non-computation weeks should roll back to recent computation types instead of introducing unrelated content.
   - Wrong-question types should reappear next day, on weekends, and at unit wrap-up.

## Product Concepts To Preserve

Preserve these mainly as identity, tone, and future-direction signals unless another current spec promotes them into active scope.

- “我的计算森林” identity, evolved from “计算小树苗”.
- “每天5分钟，种下属于你的成长森林”.
- Tree growth as gentle progress feedback.
- A semester/holiday grows one tree; primary school years can grow a forest.
- Tree species choice as a source of ownership and curiosity.
- Wrong questions are “small stones” to move away.
- Holiday dormant/rest mode.
- Growth over comparison.
- “无论从几年级开始，今天就是最好的开始”.

## Product Concepts To Defer

- Full multi-textbook knowledge graph.
- Complete student/home app.
- Complete holiday-mode workflows.
- Voice input / ASR integration.
- Photo upload / OCR grading pipeline.
- 30+ tree species full knowledge cards.
- Six-year graduation album and persistent forest account system.
- Offline and 2G support.
- Heavy animations, badges, rewards, and teacher gifts.

## PM Interpretation

The teacher material is strongest when translated into this MVP question:

> Can a teacher use a short, progress-aligned calculation exercise to see error causes and decide what to explain next?

The first build should prove this before expanding into the full forest ecosystem.

The May 2 revision especially strengthens three planning directions that are worth preserving now:

1. Forest growth should be treated as a lightweight motivation and persistence layer on top of diagnosis, not as a separate gamified product.
2. Guidance must remain textbook-first, while still leaving room for exploration/challenge modes for stronger learners.
3. Multimodal input is strategically important, but should enter as data-model and workflow readiness before it becomes a core engineering dependency.
4. Future practice generation should be constrained by teaching progress, rolling review rules, and short-duration practice expectations, rather than free-form question generation.

## Spirit That Must Show Up In Outward Docs

- 这是“我的计算森林”，不是一个只会报错因的批改器。
- 产品核心是长期坚持、温和陪伴、包容任何起点，而不是竞争和打卡压力。
- 教师是主导者，AI 是能加快诊断、讲评和练习准备的助手。
- 孩子做错时先被引导思考，再被帮助修正，不被直接扔答案。
- 树种、鼓励语和森林隐喻都应该服务教育价值，而不只是装饰。
