from __future__ import annotations

import json
import re
from pathlib import Path

from app.db import get_db

_KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge"

# FTS5 special operators that cause syntax errors if unescaped
_FTS5_UNSAFE = re.compile(r"""[^a-zA-Z0-9\u4e00-\u9fff\s]""")


async def init_knowledge_index() -> None:
    async with get_db() as db:
        await db.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                path, title, content,
                tokenize='trigram'
            )
        """
        )
        count = await db.execute("SELECT count(*) FROM knowledge_fts")
        if (await count.fetchone())[0] > 0:
            return

        for md_file in _KNOWLEDGE_DIR.rglob("*.md"):
            path = str(md_file.relative_to(_KNOWLEDGE_DIR))
            content = md_file.read_text(encoding="utf-8")
            title = (
                content.split("\n")[0].replace("#", "").strip()
                if content
                else path
            )
            await db.execute(
                "INSERT INTO knowledge_fts (path, title, content) VALUES (?, ?, ?)",
                (path, title, content),
            )
        await db.commit()


async def search_knowledge(query: str, limit: int = 5) -> list[dict]:
    safe_query = _FTS5_UNSAFE.sub("", query).strip()
    if not safe_query:
        return []
    async with get_db() as db:
        if len(safe_query) >= 3:
            cursor = await db.execute(
                """
                SELECT path, title, content
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (safe_query, limit),
            )
        else:
            cursor = await db.execute(
                """
                SELECT path, title, content
                FROM knowledge_fts
                WHERE content LIKE ?
                LIMIT ?
                """,
                (f"%{safe_query}%", limit),
            )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            snippet = _extract_snippet(row[2], safe_query)
            results.append({"path": row[0], "title": row[1], "snippet": snippet})
        return results


def _extract_snippet(content: str, query: str, context_chars: int = 80) -> str:
    idx = content.find(query)
    if idx == -1:
        return content[:context_chars * 2] + ("..." if len(content) > context_chars * 2 else "")
    start = max(0, idx - context_chars)
    end = min(len(content), idx + len(query) + context_chars)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    return prefix + content[start:end] + suffix


async def list_knowledge_points(
    unit_number: int | None = None,
) -> list[dict]:
    async with get_db() as db:
        if unit_number:
            cursor = await db.execute(
                "SELECT * FROM knowledge_points WHERE unit_number = ? ORDER BY sort_order",
                (unit_number,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM knowledge_points ORDER BY unit_number, sort_order"
            )
        return [dict(r) for r in await cursor.fetchall()]


def _parse_exercise_type_row(r: dict) -> dict:
    r["difficulty_range"] = json.loads(r.get("difficulty_range") or "[]")
    r["related_error_codes"] = json.loads(r.get("related_error_codes") or "[]")
    r["knowledge_points"] = json.loads(r.get("knowledge_points") or "[]")
    r["grade_range"] = json.loads(r.get("grade_range") or "[]")
    r["is_active"] = bool(r.get("is_active", 1))
    return r


async def list_exercise_types(category: str | None = None) -> list[dict]:
    async with get_db() as db:
        if category:
            cursor = await db.execute(
                "SELECT * FROM exercise_types WHERE category = ? ORDER BY sort_order, id",
                (category,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM exercise_types ORDER BY sort_order, id"
            )
        rows = [dict(r) for r in await cursor.fetchall()]

    cats: dict[str, dict] = {}
    for row in rows:
        r = _parse_exercise_type_row(row)
        if r["parent_id"] is None:
            cats[r["id"]] = {
                "id": r["id"],
                "name": r["name"],
                "code": r["code"],
                "description": r.get("description", ""),
                "sort_order": r.get("sort_order", 0),
                "subtypes": [],
            }
        else:
            parent = cats.get(r["parent_id"])
            if parent:
                parent["subtypes"].append(r)

    return list(cats.values())


async def get_exercise_type(type_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM exercise_types WHERE id = ?", (type_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        result = _parse_exercise_type_row(dict(row))

        if result["parent_id"] is not None:
            pcursor = await db.execute(
                "SELECT * FROM exercise_types WHERE id = ?", (result["parent_id"],)
            )
            parent_row = await pcursor.fetchone()
            if parent_row:
                result["parent_name"] = dict(parent_row)["name"]
    return result
