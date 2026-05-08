from __future__ import annotations

import asyncio
import os
import re
import shutil
import tempfile
import uuid
from datetime import date
from pathlib import Path

import jinja2

from app.db import get_db

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "pdfs"

XELATEX_BIN = Path.home() / ".TinyTeX" / "bin" / "x86_64-linux" / "xelatex"

_difficulty_labels = {"A": "基础巩固", "B": "能力提升", "C": "挑战冲刺", "mixed": "综合"}


def _render_tex(
    *,
    class_name: str,
    student_name: str | None,
    title: str,
    difficulty: str,
    problems: list[dict],
) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
        comment_start_string="<#",
        comment_end_string="#>",
    )
    template = env.get_template("homework.tex")

    diff_label = _difficulty_labels.get(difficulty, "综合")
    if len(set(p["difficulty"] for p in problems)) > 1:
        diff_label = "综合"

    for p in problems:
        raw = p.get("problem_plain") or p.get("problem", "")
        p["problem"] = _to_latex_math(raw)

    return template.render(
        class_name=class_name,
        student_name=student_name or "",
        title=title,
        date=date.today().strftime("%Y-%m-%d"),
        difficulty=diff_label,
        problems=problems,
    )


def _escape_tex(text: str) -> str:
    if "$" in text:
        return text
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


_FRAC_RE = re.compile(r"(\d+)/(\d+)")  # fraction pattern: 2/3, 12/5
_RATIO_RE = re.compile(r"(\d+):(\d+)")  # ratio pattern: 3:2
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef，。、；：？！\u201c\u201d\u2018\u2019（）《》【】]")


def _to_latex_math(text: str) -> str:
    """Convert plain-text math to LaTeX.  Already-LaTeX text passes through.

    Pure math expressions are wrapped in a single ``$...$``.
    Mixed Chinese+math text keeps Chinese outside math mode and only
    wraps the math portions (fractions, operators) in inline ``$...$``.
    """
    if "$" in text or "\\" in text:
        return text

    has_cjk = bool(_CJK_RE.search(text))

    if not has_cjk:
        # Pure math expression — wrap entirely in $...$
        s = text
        s = _FRAC_RE.sub(r"\\dfrac{\1}{\2}", s)
        s = s.replace("×", "\\times ").replace("÷", "\\div ")
        s = s.replace("π", "\\pi ")
        s = s.replace("cm²", "\\text{cm}^2").replace("m²", "\\text{m}^2")
        s = _RATIO_RE.sub(r"\1\\!:\\!\2", s)
        return f"${s}$"

    # Mixed Chinese + math — keep Chinese outside math mode
    s = text
    # Replace fractions with inline $dfrac{}{}$
    s = _FRAC_RE.sub(lambda m: f"$\\dfrac{{{m.group(1)}}}{{{m.group(2)}}}$", s)
    # Replace operators with inline math
    s = s.replace("×", "$\\times$").replace("÷", "$\\div$")
    s = s.replace("π", "$\\pi$")
    s = s.replace("cm²", "$\\text{cm}^2$").replace("m²", "$\\text{m}^2$")
    if "cm" in s and "$\\text{cm}" not in s:
        s = s.replace("cm", "$\\text{cm}$")
    s = _RATIO_RE.sub(lambda m: f"${m.group(1)}\\!:\\!{m.group(2)}$", s)
    # Merge adjacent $...$$...$ into a single $...$
    prev = ""
    while prev != s:
        prev = s
        s = re.sub(r"\$([^$]*?)\$\$([^$]*?)\$", r"$\1\2$", s)
    return s


async def _run_xelatex(work_dir: str, tex_file: Path) -> None:
    for pass_num in range(2):
        proc = await asyncio.create_subprocess_exec(
            str(XELATEX_BIN),
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", work_dir,
            str(tex_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode != 0:
            log_file = Path(work_dir) / "homework.log"
            log_content = log_file.read_text(encoding="utf-8", errors="replace")[-2000:] if log_file.exists() else ""
            raise RuntimeError(
                f"xelatex failed (exit {proc.returncode}, pass {pass_num+1}). Log tail:\n{log_content}"
            )


async def compile_tex_to_pdf(tex_source: str, output_path: Path) -> Path:
    work_dir = tempfile.mkdtemp(prefix="calc_forest_tex_")
    try:
        tex_file = Path(work_dir) / "homework.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        await _run_xelatex(work_dir, tex_file)

        pdf_file = Path(work_dir) / "homework.pdf"
        if not pdf_file.exists():
            raise RuntimeError("xelatex produced no PDF output")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(pdf_file), str(output_path))
        return output_path

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def generate_homework_pdf(
    homework_id: str,
    class_id: str,
    class_name: str = "",
    student_id: str | None = None,
    student_name: str | None = None,
    title: str = "课后练习",
) -> str:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM homework WHERE id = ?",
            (homework_id,),
        )
        hw = await cursor.fetchone()
        if not hw:
            raise ValueError(f"Homework {homework_id} not found")

        cursor = await db.execute(
            "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problems = [dict(r) for r in await cursor.fetchall()]

    if not class_name:
        async with get_db() as db:
            cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
            row = await cursor.fetchone()
            class_name = row["name"] if row else class_id

    tex_source = _render_tex(
        class_name=class_name,
        student_name=student_name,
        title=title,
        difficulty=problems[0]["difficulty"] if problems else "A",
        problems=problems,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{student_id}" if student_id else "_class"
    pdf_filename = f"hw_{homework_id}{suffix}.pdf"
    pdf_path = OUTPUT_DIR / pdf_filename

    await compile_tex_to_pdf(tex_source, pdf_path)

    async with get_db() as db:
        await db.execute(
            """INSERT INTO homework_pdfs (id, homework_id, class_id, student_id, pdf_path, pdf_type)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                uuid.uuid4().hex[:12],
                homework_id,
                class_id,
                student_id,
                str(pdf_path),
                "individual" if student_id else "class",
            ),
        )
        await db.commit()

    return str(pdf_path)


async def batch_generate_pdfs(
    homework_id: str,
    class_id: str,
    class_name: str = "",
    title: str = "课后练习",
    student_ids: list[str] | None = None,
) -> list[str]:
    if not class_name:
        async with get_db() as db:
            cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
            row = await cursor.fetchone()
            class_name = row["name"] if row else class_id

    if student_ids is None:
        async with get_db() as db:
            cursor = await db.execute("SELECT id FROM students WHERE class_id = ?", (class_id,))
            student_ids = [r["id"] for r in await cursor.fetchall()]

    results = []
    for sid in student_ids:
        sname = sid
        async with get_db() as db:
            cursor = await db.execute("SELECT name FROM students WHERE id = ?", (sid,))
            row = await cursor.fetchone()
            if row:
                sname = row["name"]
        try:
            path = await generate_homework_pdf(
                homework_id=homework_id,
                class_id=class_id,
                class_name=class_name,
                student_id=sid,
                student_name=sname,
                title=title,
            )
            results.append(path)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("PDF failed for %s: %s", sid, e)
            results.append("")

    return [r for r in results if r]


async def get_homework_pdf_paths(homework_id: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM homework_pdfs WHERE homework_id = ?",
            (homework_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]
