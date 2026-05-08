"""RAG-augmented knowledge retrieval for math problem generation."""
from __future__ import annotations

import json
from app.db import get_db


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    d = dict(row)
    for key in ("prerequisite_ids", "calc_subtypes", "error_codes", "review_types"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


async def get_knowledge_points_by_error_code(error_code: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM knowledge_points WHERE error_code = ? ORDER BY sort_order",
            (error_code,),
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]


async def get_knowledge_point_by_id(kp_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM knowledge_points WHERE id = ?", (kp_id,),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None


async def get_related_concepts(kp_id: str, max_depth: int = 2) -> list[dict]:
    visited: set[str] = {kp_id}
    result: list[dict] = []
    frontier = [kp_id]

    async with get_db() as db:
        for _ in range(max_depth):
            next_frontier: list[str] = []
            for fid in frontier:
                cursor = await db.execute(
                    """SELECT cr.*, kp_s.topic AS source_topic, kp_t.topic AS target_topic
                       FROM concept_relations cr
                       JOIN knowledge_points kp_s ON cr.source_id = kp_s.id
                       JOIN knowledge_points kp_t ON cr.target_id = kp_t.id
                       WHERE cr.source_id = ? OR cr.target_id = ?""",
                    (fid, fid),
                )
                for row in await cursor.fetchall():
                    rd = _row_to_dict(row)
                    other_id = rd["target_id"] if rd["source_id"] == fid else rd["source_id"]
                    if other_id not in visited:
                        visited.add(other_id)
                        next_frontier.append(other_id)
                        kp_cursor = await db.execute(
                            "SELECT * FROM knowledge_points WHERE id = ?", (other_id,),
                        )
                        kp_row = await kp_cursor.fetchone()
                        if kp_row:
                            entry = _row_to_dict(kp_row)
                            entry["relation_from"] = fid
                            entry["relation_type"] = rd["relation_type"]
                            result.append(entry)
            frontier = next_frontier
            if not frontier:
                break

    return result


async def get_example_problems(
    error_code: str, difficulty: str = "B", limit: int = 3,
) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM problem_bank
               WHERE error_code = ? AND difficulty = ? AND verified = 1
               ORDER BY use_count ASC LIMIT ?""",
            (error_code, difficulty, limit),
        )
        rows = await cursor.fetchall()
        if not rows:
            cursor = await db.execute(
                """SELECT * FROM problem_bank
                   WHERE error_code = ? AND verified = 1
                   ORDER BY use_count ASC LIMIT ?""",
                (error_code, limit),
            )
            rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


async def get_week_calc_type(
    week_number: int, grade: int = 6, semester: int = 1,
) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM week_calc_mapping
               WHERE week_start <= ? AND week_end >= ? AND grade = ? AND semester = ?""",
            (week_number, week_number, grade, semester),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None


async def get_prerequisites(kp_ids: list[str]) -> list[dict]:
    if not kp_ids:
        return []
    async with get_db() as db:
        placeholders = ",".join("?" * len(kp_ids))
        cursor = await db.execute(
            f"SELECT * FROM knowledge_points WHERE id IN ({placeholders})",
            kp_ids,
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]


async def build_rag_context(
    error_codes: list[str],
    difficulty: str = "B",
    week_number: int | None = None,
) -> dict:
    knowledge_points: list[dict] = []
    for ec in error_codes:
        knowledge_points.extend(await get_knowledge_points_by_error_code(ec))

    related_concepts: list[dict] = []
    seen: set[str] = set()
    for kp in knowledge_points[:5]:
        related = await get_related_concepts(kp["id"], max_depth=1)
        for r in related:
            if r["id"] not in seen:
                seen.add(r["id"])
                related_concepts.append(r)

    example_problems: list[dict] = []
    for ec in error_codes:
        example_problems.extend(await get_example_problems(ec, difficulty, limit=3))

    week_context = None
    if week_number is not None:
        week_context = await get_week_calc_type(week_number)

    prereq_ids: list[str] = []
    for kp in knowledge_points:
        for pid in kp.get("prerequisite_ids", []):
            if pid and pid not in prereq_ids:
                prereq_ids.append(pid)
    prerequisites = await get_prerequisites(prereq_ids)

    return {
        "knowledge_points": knowledge_points,
        "related_concepts": related_concepts,
        "example_problems": example_problems,
        "week_context": week_context,
        "prerequisites": prerequisites,
    }


async def get_knowledge_context(
    error_codes: list[str],
    difficulty: str = "B",
    week_number: int | None = None,
) -> dict:
    return await build_rag_context(error_codes, difficulty, week_number)
