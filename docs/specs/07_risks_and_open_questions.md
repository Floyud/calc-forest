# Risks And Open Questions

## Risks

1. **Diagnosis ambiguity**: final answers alone often cannot identify the true thinking process.
   - Mitigation: use confidence, evidence, and teacher review; request steps when needed.

2. **Scope creep from teacher vision**: full textbook coverage, holiday mode, and home practice are attractive but too large for MVP.
   - Mitigation: keep those in roadmap and competition narrative, not current implementation.

3. **Game mechanics creating pressure**: streaks and growth rewards can conflict with no-pressure principles.
   - Mitigation: use gentle progress feedback, not ranking or forced streaks.

4. **API/document drift**: old multi-endpoint notes can confuse implementers.
   - Mitigation: use `docs/specs/05_data_contract.md` and `Agent.md` as current contract.

5. **Overclaiming AI accuracy**: competition claims may exceed actual rule coverage.
   - Mitigation: include test results, known gaps, and teacher-review mechanism.

## Open Questions

- Which textbook/year/unit should become the first real teaching-progress demo?
- Should Dify call `POST /api/diagnose` directly, or should we add a compatibility `/api/diagnose` later?
- How many full diagnosis cases are needed for competition video credibility?
- When should the tree-growth feedback move from text to UI?
- What is the minimum real-teacher trial data we can collect safely?
