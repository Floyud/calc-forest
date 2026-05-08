# Acceptance Criteria

## PM Acceptance

- MVP scope is limited to teacher-side diagnosis.
- Product docs clearly distinguish shipped MVP from future vision.
- All outputs have teacher-review boundary.
- No ranking, forced streak, or holiday pressure is introduced.
- Product narrative clearly reflects “我的计算森林” rather than a generic correction tool.
- Error taxonomy uses `E01-E11`.

## Teacher Acceptance

- A teacher can understand the diagnosis without reading code.
- Each result explains why the system chose the error tag.
- Suggested action is practical for short classroom feedback.
- Practice vision follows the 3-5 minute constraint.

## Engineering Acceptance

- Tests pass from `development/`.
- API returns structured response for `POST /api/diagnose`.
- Practice recommendation and forest-config endpoints return structured responses.
- Synthetic demo data validates without missing fields.
- Runtime commands use `pyt0`.

## Competition Acceptance

- Materials can show AI-assisted development evidence.
- Materials can show code, prompt/workflow plan, tests, and synthetic cases.
- AI-generated content is marked or described as teacher-reviewed.
- No real student faces or sensitive data are used.

## Current Verification Command

```bash
cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
/home/lyzhang/miniconda3/envs/pyt0/bin/python -m pytest -s tests/test_diagnosis.py -q
```
