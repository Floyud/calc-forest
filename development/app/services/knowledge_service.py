from __future__ import annotations

import json
from pathlib import Path

from app.db import get_db

_KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge"


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
    async with get_db() as db:
        if len(query) >= 3:
            cursor = await db.execute(
                """
                SELECT path, title,
                       snippet(knowledge_fts, 2, '>>', '<<', '...', 20) AS snippet
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            )
        else:
            cursor = await db.execute(
                """
                SELECT path, title, '' AS snippet
                FROM knowledge_fts
                WHERE content LIKE ?
                LIMIT ?
                """,
                (f"%{query}%", limit),
            )
        rows = await cursor.fetchall()
        return [
            {"path": row[0], "title": row[1], "snippet": row[2]} for row in rows
        ]
