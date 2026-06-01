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



_FRAC_RE = re.compile(r"(\d+)/(\d+)")  # fraction pattern: 2/3, 12/5
_RATIO_RE = re.compile(r"(\d+):(\d+)")  # ratio pattern: 3:2
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef，。、；：？！\u201c\u201d\u2018\u2019（）《》【】]")


def _to_latex_math(text: str) -> str:
    """Convert plain-text math to LaTeX.  Already-LaTeX text passes through.

    Pure math expressions are wrapped in a single ``$...$``.
    Mixed Chinese+math text keeps Chinese outside math mode and only
    wraps the math portions (fractions, operators) in inline ``$...$``.
    """
    # Replace Unicode circled numbers ①-⑩ with LaTeX \textcircled
    _CIRCLED_MAP = {
        "①": r"\textcircled{1}", "②": r"\textcircled{2}", "③": r"\textcircled{3}",
        "④": r"\textcircled{4}", "⑤": r"\textcircled{5}", "⑥": r"\textcircled{6}",
        "⑦": r"\textcircled{7}", "⑧": r"\textcircled{8}", "⑨": r"\textcircled{9}",
        "⑩": r"\textcircled{10}", "⑪": r"\textcircled{11}", "⑫": r"\textcircled{12}",
    }
    for ch, rep in _CIRCLED_MAP.items():
        text = text.replace(ch, rep)

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
                f"xelatex 编译失败（退出码 {proc.returncode}，第 {pass_num+1} 次尝试）。日志尾部:\n{log_content}"
            )

async def _compile_html_fallback(output_path: Path) -> None:
    """Fallback: generate a minimal PDF using weasyprint when xelatex is unavailable."""
    import logging
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError(
            "xelatex 和 weasyprint 均不可用。请安装 TinyTeX 或运行: pip install weasyprint"
        )
    logger = logging.getLogger(__name__)
    html_content = (
        "<html><head><meta charset='UTF-8'><style>"
        "body{font-family:sans-serif;padding:20px;}"
        "h1{text-align:center;}"
        ".problem{margin:8px 0;padding:8px;border:1px solid #ddd;}"
        "</style></head><body>"
        "<h1>我的计算森林 · 数学练习</h1>"
        "<p style='text-align:center;color:#999;'>PDF（HTML 回退模式）</p>"
        "<p>LaTeX编译不可用，请安装TinyTeX以获取高质量PDF输出。</p>"
        "</body></html>"
    )
    HTML(string=html_content).write_pdf(str(output_path))
    logger.info("PDF generated via weasyprint HTML fallback: %s", output_path)


async def compile_tex_to_pdf(tex_source: str, output_path: Path) -> Path:
    work_dir = tempfile.mkdtemp(prefix="calc_forest_tex_")
    try:
        tex_file = Path(work_dir) / "homework.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        if not XELATEX_BIN.exists():
            raise RuntimeError(f"未找到 xelatex: {XELATEX_BIN}")

        try:
            await _run_xelatex(work_dir, tex_file)
        except (RuntimeError, FileNotFoundError, OSError) as e:
            import logging
            logging.getLogger(__name__).warning("xelatex failed (%s), falling back to weasyprint", e)
            await _compile_html_fallback(output_path)
            return output_path

        pdf_file = Path(work_dir) / "homework.pdf"
        if not pdf_file.exists():
            raise RuntimeError("xelatex 未生成 PDF 输出")

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
            raise ValueError(f"作业 {homework_id} 不存在")

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


async def get_class_homework_pdfs(class_id: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT hp.*, h.grade, h.status as hw_status, h.created_at as hw_created
               FROM homework_pdfs hp
               JOIN homework h ON hp.homework_id = h.id
               WHERE hp.class_id = ?
               ORDER BY h.created_at DESC, hp.student_id""",
            (class_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_pdf_record(pdf_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM homework_pdfs WHERE id = ?", (pdf_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Student Report PDF
# ---------------------------------------------------------------------------

_REPORT_TYPE_LABELS = {
    "weekly": "周报",
    "monthly": "月报",
    "unit": "单元报告",
    "semester": "学期报告",
    "full_year": "学年报告",
}

_STAGE_LABELS = {
    "seed": "种子",
    "sprout": "嫩芽",
    "first_leaf": "长叶",
    "taller": "拔节",
    "branching": "枝繁",
    "sturdy": "茂盛",
    "bud": "含苞",
    "flowering": "开花",
    "mature": "成熟",
}

_ERROR_LABELS = {
    "E01": "基础事实错误",
    "E02": "进位错误",
    "E03": "退位错误",
    "E04": "数位对齐错误",
    "E05": "运算顺序错误",
    "E06": "小数点/分数单位错误",
    "E07": "抄题/转写错误",
    "E08": "步骤遗漏",
    "E09": "算理理解不足",
    "E10": "审题与单位理解错误",
    "E11": "习惯性未验算",
    "E99": "暂未识别错因",
}

_EMOTIONAL_ICONS = {
    "thriving": r"$\ddot\smile$",
    "stable": r"$\smile$",
    "improving": r"$\Rightarrow$",
    "struggling": r"$\frown$",
    "wilting": r"$\ddot\frown$",
}

_EMOTIONAL_LABELS = {
    "thriving": "茁壮成长",
    "stable": "稳步前进",
    "improving": "进步明显",
    "struggling": "需要关注",
    "wilting": "需要鼓励",
}

_ABILITY_DIMENSION_DEFS = [
    ("计算准确率", "accuracy"),
    ("运算速度", "speed"),
    ("步骤规范", "steps"),
    ("验算习惯", "checking"),
    ("知识迁移", "transfer"),
]


def _escape_tex(text: str) -> str:
    """Escape LaTeX special characters in plain text."""
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
        .replace("$", "\\$")
    )


def _compute_emotional_state(
    weekly_accuracy: list[float],
    overall_accuracy: float,
) -> tuple[str, str]:
    """Return (icon_tex, label_cn) for emotional state."""
    if not weekly_accuracy or len(weekly_accuracy) < 2:
        if overall_accuracy >= 0.9:
            state = "thriving"
        elif overall_accuracy >= 0.4:
            state = "stable"
        else:
            state = "wilting"
    else:
        recent = weekly_accuracy[-3:] if len(weekly_accuracy) >= 3 else weekly_accuracy
        accs = recent
        if len(accs) >= 2 and accs[-1] > accs[-2] + 0.1:
            state = "improving"
        elif len(accs) >= 2 and accs[-1] < accs[-2] - 0.15:
            state = "struggling"
        elif overall_accuracy >= 0.8:
            state = "thriving"
        elif overall_accuracy >= 0.4:
            state = "stable"
        else:
            state = "wilting"
    return _EMOTIONAL_ICONS.get(state, r"$\smile$"), _EMOTIONAL_LABELS.get(state, "稳步前进")


def _render_report_tex(**data: object) -> str:
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
    template = env.get_template("report.tex")
    return template.render(**data)


def _render_class_report_tex(**data: object) -> str:
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
    template = env.get_template("class_report.tex")
    return template.render(**data)


async def generate_student_report_pdf(
    student_id: str,
    report_type: str = "weekly",
    period_start: str | None = None,
    period_end: str | None = None,
) -> str:
    """Generate a forest-themed periodic report PDF for a student.

    Returns the path to the generated PDF file.
    """
    import json

    report_type_label = _REPORT_TYPE_LABELS.get(report_type, "成长报告")

    async with get_db() as db:
        # 1. Student info
        cursor = await db.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student_row = await cursor.fetchone()
        if not student_row:
            raise ValueError(f"学生 {student_id} 不存在")
        student = dict(student_row)
        student_name = _escape_tex(student["name"])

        # 2. Class name
        cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (student["class_id"],))
        class_row = await cursor.fetchone()
        class_name = _escape_tex(class_row["name"]) if class_row else student["class_id"]

        # 3. Period defaults
        if not period_end:
            period_end = date.today().isoformat()
        if not period_start:
            from datetime import timedelta
            if report_type == "weekly":
                period_start = (date.today() - timedelta(days=7)).isoformat()
            elif report_type == "monthly":
                period_start = (date.today() - timedelta(days=30)).isoformat()
            elif report_type == "semester":
                period_start = (date.today() - timedelta(days=138)).isoformat()
            elif report_type == "full_year":
                period_start = (date.today() - timedelta(days=276)).isoformat()
            else:
                period_start = (date.today() - timedelta(days=14)).isoformat()

        # 4. Diagnosis history for the period
        cursor = await db.execute(
            """SELECT * FROM diagnosis_history
               WHERE student_id = ? AND created_at >= ? AND created_at <= ?
               ORDER BY created_at""",
            (student_id, period_start, period_end + " 23:59:59"),
        )
        diag_rows = [dict(r) for r in await cursor.fetchall()]

        total_problems = len(diag_rows)
        correct_count = sum(1 for r in diag_rows if r["is_correct"])
        accuracy_rate = round(correct_count / total_problems * 100, 1) if total_problems > 0 else 0.0
        accuracy_frac = round(correct_count / total_problems, 4) if total_problems > 0 else 0.0

        # 5. Error distribution
        cursor = await db.execute(
            """SELECT error_code,
                      SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as error_count
               FROM diagnosis_history
               WHERE student_id = ? AND created_at >= ? AND created_at <= ?
                 AND is_correct = 0 AND error_code != 'OK'
               GROUP BY error_code
               ORDER BY error_count DESC""",
            (student_id, period_start, period_end + " 23:59:59"),
        )
        error_dist_rows = [dict(r) for r in await cursor.fetchall()]

        error_distribution = []
        for row in error_dist_rows:
            code = row["error_code"]
            cnt = row["error_count"]
            error_distribution.append({
                "code": code,
                "label": _ERROR_LABELS.get(code, code),
                "count": cnt,
                "percentage": round(cnt / total_problems * 100, 1) if total_problems > 0 else 0.0,
            })

        # 6. Top 3 errors
        top_errors = []
        for ed in error_distribution[:3]:
            top_errors.append({
                "code": ed["code"],
                "label": ed["label"],
                "description": _ERROR_LABELS.get(ed["code"], ""),
            })

        # 7. Previous period comparison
        # Get the period before this one (same length)
        from datetime import datetime
        try:
            ps_dt = datetime.fromisoformat(period_start)
            pe_dt = datetime.fromisoformat(period_end)
            delta = pe_dt - ps_dt
            prev_end = period_start
            prev_start = (ps_dt - delta).isoformat()
        except (ValueError, TypeError):
            prev_start = None
            prev_end = None

        prev_comparison = []
        if prev_start and prev_end:
            cursor = await db.execute(
                """SELECT COUNT(*) as total,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM diagnosis_history
                   WHERE student_id = ? AND created_at >= ? AND created_at <= ?""",
                (student_id, prev_start, prev_end + " 23:59:59"),
            )
            prev_row = await cursor.fetchone()
            if prev_row and prev_row["total"] and prev_row["total"] > 0:
                prev_acc = round(prev_row["correct"] / prev_row["total"] * 100, 1)
                diff = round(accuracy_rate - prev_acc, 1)
                if diff > 0:
                    indicator = f"$\\uparrow$ +{diff}%"
                elif diff < 0:
                    indicator = f"$\\downarrow$ {diff}%"
                else:
                    indicator = "$\\rightarrow$ 持平"
                prev_comparison.append({
                    "label": "正确率变化",
                    "indicator": indicator,
                })

        # 8. Accuracy trend (weekly or monthly depending on report type)
        if report_type in ("semester", "full_year"):
            # Monthly resolution for long-period reports
            cursor = await db.execute(
                """SELECT
                    CAST(strftime('%m', created_at) AS INTEGER) as period_num,
                    strftime('%Y-%m', created_at) as period_label,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM diagnosis_history
                   WHERE student_id = ? AND created_at >= ? AND created_at <= ?
                   GROUP BY period_label
                   ORDER BY period_label""",
                (student_id, period_start, period_end + " 23:59:59"),
            )
        else:
            # Weekly resolution for short-period reports
            cursor = await db.execute(
                """SELECT
                    CAST(strftime('%W', created_at) AS INTEGER) as week_num,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM diagnosis_history
                   WHERE student_id = ? AND created_at >= ? AND created_at <= ?
                   GROUP BY week_num
                   ORDER BY week_num""",
                (student_id, period_start, period_end + " 23:59:59"),
            )
        trend_rows = [dict(r) for r in await cursor.fetchall()]

        accuracy_trend = []
        trend_coordinates = ""
        trend_xticks = ""
        trend_xlabels = ""
        if trend_rows:
            for i, tr in enumerate(trend_rows):
                acc = round(tr["correct"] / tr["total"] * 100, 1) if tr["total"] > 0 else 0.0
                accuracy_trend.append({"week": i + 1, "accuracy": acc})
                if i > 0:
                    trend_coordinates += " "
                    trend_xticks += ","
                    trend_xlabels += ","
                trend_coordinates += f"({i + 1},{acc})"
                trend_xticks += str(i + 1)
                if report_type in ("semester", "full_year") and "period_label" in tr:
                    trend_xlabels += tr["period_label"]
                else:
                    trend_xlabels += f"第{i + 1}周"

        trend_highlight = ""
        if accuracy_trend:
            last_pt = accuracy_trend[-1]
            trend_highlight = (
                f"\\draw[warmgold, thick, dashed] "
                f"(axis cs:{last_pt['week']},0) -- (axis cs:{last_pt['week']},{last_pt['accuracy']});"
            )

        trend_label_x = 1 if not accuracy_trend else accuracy_trend[-1]["week"] + 0.5
        trend_xlabel = "月份" if report_type in ("semester", "full_year") else "周次"

        # 9. Growth stage
        cursor = await db.execute(
            """SELECT days_completed, current_stage
               FROM student_cycle_progress
               WHERE student_id = ?
               ORDER BY days_completed DESC
               LIMIT 1""",
            (student_id,),
        )
        progress_row = await cursor.fetchone()
        if progress_row:
            days_completed = progress_row["days_completed"]
            current_stage = progress_row["current_stage"]
        else:
            days_completed = 0
            current_stage = "seed"
        growth_stage = _STAGE_LABELS.get(current_stage, "种子")

        # 10. Ability dimensions (computed from error stats)
        cursor = await db.execute(
            """SELECT error_code, total_attempts, correct_count
               FROM student_error_stats
               WHERE student_id = ?""",
            (student_id,),
        )
        stat_rows = [dict(r) for r in await cursor.fetchall()]
        total_attempts_global = sum(r["total_attempts"] for r in stat_rows) or 1
        total_correct_global = sum(r["correct_count"] for r in stat_rows)

        dim_colors = ["forestgreen", "warmgold", "skyblue", "softred", "deepgreen"]
        ability_dimensions = []
        for i, (dim_name, _dim_key) in enumerate(_ABILITY_DIMENSION_DEFS):
            if i == 0:
                # 计算准确率 → based on overall accuracy
                score = round(accuracy_rate, 1)
            elif i == 1:
                # 运算速度 → proxy: practice days / goal
                score = min(100, round(days_completed / 30 * 100, 1))
            elif i == 2:
                # 步骤规范 → proxy: inverse of E08 rate
                e08 = next((r for r in stat_rows if r["error_code"] == "E08"), None)
                if e08 and e08["total_attempts"] > 0:
                    e08_rate = (e08["total_attempts"] - e08["correct_count"]) / e08["total_attempts"]
                    score = round((1 - e08_rate) * 100, 1)
                else:
                    score = 85.0
            elif i == 3:
                # 验算习惯 → proxy: inverse of E11 rate
                e11 = next((r for r in stat_rows if r["error_code"] == "E11"), None)
                if e11 and e11["total_attempts"] > 0:
                    e11_rate = (e11["total_attempts"] - e11["correct_count"]) / e11["total_attempts"]
                    score = round((1 - e11_rate) * 100, 1)
                else:
                    score = 80.0
            else:
                # 知识迁移 → proxy: accuracy on mixed error codes
                score = round(total_correct_global / total_attempts_global * 100, 1) if total_attempts_global > 0 else 70.0

            ability_dimensions.append({
                "name": dim_name,
                "score": score,
                "max_score": 100,
                "frac": round(score / 100, 4),
                "color": dim_colors[i % len(dim_colors)],
                "bar_width": "10cm",
            })

        # 11. Milestones (from cycle progress changes)
        cursor = await db.execute(
            """SELECT last_practice_date, current_stage, days_completed
               FROM student_cycle_progress
               WHERE student_id = ?
               ORDER BY days_completed""",
            (student_id,),
        )
        ms_rows = [dict(r) for r in await cursor.fetchall()]

        milestones = []
        if ms_rows:
            n = len(ms_rows)
            for i, ms in enumerate(ms_rows):
                y_pos = round(i * 1.2, 2)
                stage_cn = _STAGE_LABELS.get(ms["current_stage"], ms["current_stage"])
                desc = f"小树苗在第 {ms['days_completed']} 天成长为「{stage_cn}」阶段"
                milestones.append({
                    "date": (ms.get("last_practice_date") or "")[:10],
                    "description": desc,
                    "y_pos": y_pos,
                })
        else:
            # Generate a default milestone from current state
            milestones.append({
                "date": period_end[:10],
                "description": f"小树苗刚刚种下，目前是「{growth_stage}」阶段",
                "y_pos": 0,
            })

        timeline_height = max(1.2 * len(milestones), 1.5)

        # 12. Recommendations
        recommendations = []
        rec_bg_colors = ["forestgreen!8", "warmgold!10", "skyblue!10"]
        rec_fg_colors = ["forestgreen", "warmgold!80!black", "skyblue!70!black"]
        if error_distribution:
            for i, ed in enumerate(error_distribution[:3]):
                priority = 1 if i == 0 else 2
                recommendations.append({
                    "priority": priority,
                    "area": f"{ed['code']} {ed['label']}",
                    "description": f"建议加强{ed['label']}方面的针对性练习，本周共出现 {ed['count']} 次。",
                    "bg_color": rec_bg_colors[i % len(rec_bg_colors)],
                    "fg_color": rec_fg_colors[i % len(rec_fg_colors)],
                })
        else:
            recommendations.append({
                "priority": 2,
                "area": "综合练习",
                "description": "继续保持良好的练习习惯，适当增加挑战题。",
                "bg_color": "forestgreen!8",
                "fg_color": "forestgreen",
            })

        # 13. Encouragement
        if accuracy_rate >= 90:
            encouragement = f"太棒了，{student['name']}！你的小树苗正在茁壮成长，继续加油！"
        elif accuracy_rate >= 75:
            encouragement = f"{student['name']}，你做得很好！每一次练习都是对小树苗的精心浇灌。"
        elif accuracy_rate >= 60:
            encouragement = f"{student['name']}，小树苗正在努力生长！坚持练习，你会看到它越来越高。"
        else:
            encouragement = f"{student['name']}，小树苗需要更多的阳光和水分。别着急，我们一起慢慢来！"

        encouragement = _escape_tex(encouragement)

        # 14. Emotional state
        weekly_accs = [t["accuracy"] / 100.0 for t in accuracy_trend] if accuracy_trend else []
        emotional_icon, emotional_label = _compute_emotional_state(weekly_accs, accuracy_rate / 100.0 if total_problems > 0 else 0.5)

        # 15. Bar chart data
        error_x_coords = ""
        error_bar_data = ""
        chart_ymax = 5
        if error_distribution:
            for i, ed in enumerate(error_distribution[:8]):  # max 8 bars
                if i > 0:
                    error_x_coords += ","
                error_x_coords += f"{ed['code']}"
                error_bar_data += f"({ed['code']},{ed['count']}) "
            chart_ymax = max(max(ed["count"] for ed in error_distribution) + 2, 5)

        # 16. Render
        tex_source = _render_report_tex(
            student_name=student_name,
            class_name=class_name,
            report_type_label=report_type_label,
            period_start=period_start,
            period_end=period_end,
            total_problems=total_problems,
            correct_count=correct_count,
            accuracy_rate=accuracy_rate,
            accuracy_frac=accuracy_frac,
            growth_stage=growth_stage,
            days_completed=days_completed,
            emotional_icon=emotional_icon,
            emotional_label=emotional_label,
            error_distribution=error_distribution,
            top_errors=top_errors,
            prev_comparison=prev_comparison,
            accuracy_trend=accuracy_trend,
            trend_coordinates=trend_coordinates,
            trend_xticks=trend_xticks,
            trend_xlabels=trend_xlabels,
            trend_highlight=trend_highlight,
            trend_label_x=trend_label_x,
            trend_xlabel=trend_xlabel,
            ability_dimensions=ability_dimensions,
            milestones=milestones,
            timeline_height=timeline_height,
            recommendations=recommendations,
            encouragement=encouragement,
            generated_date=date.today().strftime("%Y-%m-%d"),
            error_x_coords=error_x_coords,
            error_bar_data=error_bar_data,
            chart_ymax=chart_ymax,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"report_{student_id}_{date.today().strftime('%Y%m%d')}.pdf"
    pdf_path = OUTPUT_DIR / pdf_filename

    await compile_tex_to_pdf(tex_source, pdf_path)

    return str(pdf_path)


async def list_student_reports(student_id: str) -> list[dict]:
    """List all generated report PDFs for a student."""
    pattern = f"report_{student_id}_*.pdf"
    results = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.glob(pattern), reverse=True):
            results.append({
                "filename": f.name,
                "path": str(f),
                "student_id": student_id,
                "generated_date": f.stem.split("_")[-1],
            })
    return results


# ---------------------------------------------------------------------------
# Class Report PDF
# ---------------------------------------------------------------------------

_CLASS_REPORT_TYPE_LABELS = {
    "weekly": "周报",
    "monthly": "月度报告",
    "semester": "学期报告",
    "full_year": "学年报告",
}

_WEAK_SPOT_COLORS = ["softred", "warmgold!80!black", "skyblue!70!black", "forestgreen", "bark"]


async def generate_class_report_pdf(
    class_id: str,
    report_type: str = "monthly",
    period_start: str | None = None,
    period_end: str | None = None,
) -> str:
    from datetime import datetime, timedelta

    report_type_label = _CLASS_REPORT_TYPE_LABELS.get(report_type, "班级报告")

    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        class_row = await cursor.fetchone()
        if not class_row:
            raise ValueError(f"Class {class_id} not found")
        class_data = dict(class_row)
        class_name = _escape_tex(class_data["name"])

        if not period_end:
            period_end = date.today().isoformat()
        if not period_start:
            if report_type == "weekly":
                period_start = (date.today() - timedelta(days=7)).isoformat()
            elif report_type == "monthly":
                period_start = (date.today() - timedelta(days=30)).isoformat()
            elif report_type == "semester":
                period_start = (date.today() - timedelta(days=138)).isoformat()
            elif report_type == "full_year":
                period_start = (date.today() - timedelta(days=276)).isoformat()
            else:
                period_start = (date.today() - timedelta(days=30)).isoformat()

        cursor = await db.execute(
            "SELECT id, name FROM students WHERE class_id = ?", (class_id,)
        )
        students = [dict(r) for r in await cursor.fetchall()]
        total_students = len(students)

        period_filter = (period_start, period_end + " 23:59:59")

        student_ids = [stu["id"] for stu in students]
        sid_placeholders = ",".join("?" for _ in student_ids)
        sid_params = student_ids

        accuracy_map: dict[str, dict] = {}
        cursor = await db.execute(
            f"""SELECT student_id,
                       COUNT(*) as total,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                  FROM diagnosis_history
                  WHERE student_id IN ({sid_placeholders})
                    AND created_at >= ? AND created_at <= ?
                  GROUP BY student_id""",
            (*sid_params, *period_filter),
        )
        for row in await cursor.fetchall():
            r = dict(row)
            accuracy_map[r["student_id"]] = r

        top_error_map: dict[str, str] = {}
        cursor = await db.execute(
            f"""SELECT student_id, error_code, COUNT(*) as cnt
                  FROM diagnosis_history
                  WHERE student_id IN ({sid_placeholders})
                    AND created_at >= ? AND created_at <= ?
                    AND is_correct = 0 AND error_code != 'OK'
                  GROUP BY student_id, error_code
                  ORDER BY student_id, cnt DESC""",
            (*sid_params, *period_filter),
        )
        seen_students: set[str] = set()
        for row in await cursor.fetchall():
            r = dict(row)
            if r["student_id"] not in seen_students:
                seen_students.add(r["student_id"])
                top_error_map[r["student_id"]] = (
                    f"{r['error_code']} {_ERROR_LABELS.get(r['error_code'], '')}"
                )

        student_stats = []
        for stu in students:
            sid = stu["id"]
            acc_row = accuracy_map.get(sid, {})
            total = acc_row.get("total") or 0
            correct = acc_row.get("correct") or 0
            acc = round(correct / total * 100, 1) if total > 0 else 0.0
            top_error = top_error_map.get(sid, "")

            student_stats.append({
                "id": sid,
                "name": _escape_tex(stu["name"]),
                "accuracy": acc,
                "total": total,
                "correct": correct,
                "top_error": top_error,
            })

        total_practice_count = sum(s["total"] for s in student_stats)
        total_correct = sum(s["correct"] for s in student_stats)
        avg_accuracy = round(total_correct / total_practice_count * 100, 1) if total_practice_count > 0 else 0.0
        avg_accuracy_frac = round(total_correct / total_practice_count, 4) if total_practice_count > 0 else 0.0

        cursor = await db.execute(
            """SELECT COUNT(DISTINCT DATE(created_at)) as days
               FROM diagnosis_history
               WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)
                 AND created_at >= ? AND created_at <= ?""",
            (class_id, *period_filter),
        )
        active_days_row = await cursor.fetchone()
        active_days = active_days_row["days"] if active_days_row else 0

        tier_excellent = [s for s in student_stats if s["accuracy"] >= 80]
        tier_good = [s for s in student_stats if 60 <= s["accuracy"] < 80]
        tier_attention = [s for s in student_stats if s["accuracy"] < 60]

        cursor = await db.execute(
            """SELECT error_code, COUNT(DISTINCT student_id) as student_count,
                      SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as error_count
               FROM diagnosis_history
               WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)
                 AND created_at >= ? AND created_at <= ?
                 AND is_correct = 0 AND error_code != 'OK'
               GROUP BY error_code
               ORDER BY error_count DESC""",
            (class_id, *period_filter),
        )
        error_dist_rows = [dict(r) for r in await cursor.fetchall()]

        error_distribution = []
        for row in error_dist_rows:
            error_distribution.append({
                "code": row["error_code"],
                "label": _ERROR_LABELS.get(row["error_code"], row["error_code"]),
                "count": row["error_count"],
                "student_count": row["student_count"],
            })

        weak_spots = []
        for i, ed in enumerate(error_distribution[:5]):
            weak_spots.append({
                "rank": i + 1,
                "code": ed["code"],
                "label": f"{ed['code']} {ed['label']}",
                "student_count": ed["student_count"],
                "suggestion": f"建议针对{ed['label']}进行专项练习，涉及 {ed['student_count']} 名学生。",
                "color": _WEAK_SPOT_COLORS[i % len(_WEAK_SPOT_COLORS)],
            })

        if report_type in ("semester", "full_year"):
            cursor = await db.execute(
                """SELECT
                    strftime('%Y-%m', created_at) as period_label,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM diagnosis_history
                   WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)
                     AND created_at >= ? AND created_at <= ?
                   GROUP BY period_label
                   ORDER BY period_label""",
                (class_id, *period_filter),
            )
        else:
            cursor = await db.execute(
                """SELECT
                    CAST(strftime('%W', created_at) AS INTEGER) as week_num,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM diagnosis_history
                   WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)
                     AND created_at >= ? AND created_at <= ?
                   GROUP BY week_num
                   ORDER BY week_num""",
                (class_id, *period_filter),
            )
        trend_rows = [dict(r) for r in await cursor.fetchall()]

        accuracy_trend = []
        trend_coordinates = ""
        trend_xticks = ""
        trend_xlabels = ""
        if trend_rows:
            for i, tr in enumerate(trend_rows):
                acc = round(tr["correct"] / tr["total"] * 100, 1) if tr["total"] > 0 else 0.0
                accuracy_trend.append({"week": i + 1, "accuracy": acc})
                if i > 0:
                    trend_coordinates += " "
                    trend_xticks += ","
                    trend_xlabels += ","
                trend_coordinates += f"({i + 1},{acc})"
                trend_xticks += str(i + 1)
                if report_type in ("semester", "full_year") and "period_label" in tr:
                    trend_xlabels += tr["period_label"]
                else:
                    trend_xlabels += f"第{i + 1}周"

        trend_highlight = ""
        if accuracy_trend:
            last_pt = accuracy_trend[-1]
            trend_highlight = (
                f"\\draw[warmgold, thick, dashed] "
                f"(axis cs:{last_pt['week']},0) -- (axis cs:{last_pt['week']},{last_pt['accuracy']});"
            )

        trend_label_x = 1 if not accuracy_trend else accuracy_trend[-1]["week"] + 0.5
        trend_xlabel = "月份" if report_type in ("semester", "full_year") else "周次"

        error_x_coords = ""
        error_bar_data = ""
        chart_ymax = 5
        if error_distribution:
            for i, ed in enumerate(error_distribution[:8]):
                if i > 0:
                    error_x_coords += ","
                error_x_coords += f"{ed['code']}"
                error_bar_data += f"({ed['code']},{ed['count']}) "
            chart_ymax = max(max(ed["count"] for ed in error_distribution) + 2, 5)

        rec_bg_colors = ["forestgreen!8", "warmgold!10", "skyblue!10"]
        rec_fg_colors = ["forestgreen", "warmgold!80!black", "skyblue!70!black"]
        recommendations = []
        if weak_spots:
            for i, ws in enumerate(weak_spots[:3]):
                priority = 1 if i == 0 else 2
                recommendations.append({
                    "priority": priority,
                    "area": ws["label"],
                    "description": ws["suggestion"],
                    "bg_color": rec_bg_colors[i % len(rec_bg_colors)],
                    "fg_color": rec_fg_colors[i % len(rec_fg_colors)],
                })
        if not recommendations:
            recommendations.append({
                "priority": 2,
                "area": "综合练习",
                "description": "班级整体表现良好，建议适当增加挑战题以保持进步。",
                "bg_color": "forestgreen!8",
                "fg_color": "forestgreen",
            })

        alerts = []
        try:
            ps_dt = datetime.fromisoformat(period_start)
            pe_dt = datetime.fromisoformat(period_end)
            delta = pe_dt - ps_dt
            prev_end = period_start
            prev_start = (ps_dt - delta).isoformat()
        except (ValueError, TypeError):
            prev_start = None
            prev_end = None

        if prev_start and prev_end:
            prev_accuracy_map: dict[str, dict] = {}
            cursor = await db.execute(
                f"""SELECT student_id,
                           COUNT(*) as total,
                           SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                      FROM diagnosis_history
                      WHERE student_id IN ({sid_placeholders})
                        AND created_at >= ? AND created_at <= ?
                      GROUP BY student_id""",
                (*sid_params, prev_start, prev_end + " 23:59:59"),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                prev_accuracy_map[r["student_id"]] = r

            for stu in student_stats:
                prev_row = prev_accuracy_map.get(stu["id"])
                if prev_row and prev_row["total"] and prev_row["total"] > 0:
                    prev_acc = round(prev_row["correct"] / prev_row["total"] * 100, 1)
                    drop = prev_acc - stu["accuracy"]
                    if drop >= 15:
                        alerts.append({
                            "student_id": stu["id"],
                            "student_name": stu["name"],
                            "description": f"正确率从 {prev_acc}% 下降至 {stu['accuracy']}%（下降 {round(drop, 1)}%），建议重点关注。"
                            + (f" 主要错因：{stu['top_error']}。" if stu["top_error"] else ""),
                        })

        tex_source = _render_class_report_tex(
            class_name=class_name,
            report_type_label=report_type_label,
            period_start=period_start,
            period_end=period_end,
            total_students=total_students,
            avg_accuracy=avg_accuracy,
            avg_accuracy_frac=avg_accuracy_frac,
            total_practice_count=total_practice_count,
            active_days=active_days,
            tier_excellent=tier_excellent,
            tier_excellent_count=len(tier_excellent),
            tier_good=tier_good,
            tier_good_count=len(tier_good),
            tier_attention=tier_attention,
            tier_attention_count=len(tier_attention),
            error_distribution=error_distribution,
            error_x_coords=error_x_coords,
            error_bar_data=error_bar_data,
            chart_ymax=chart_ymax,
            accuracy_trend=accuracy_trend,
            trend_coordinates=trend_coordinates,
            trend_xticks=trend_xticks,
            trend_xlabels=trend_xlabels,
            trend_highlight=trend_highlight,
            trend_label_x=trend_label_x,
            trend_xlabel=trend_xlabel,
            weak_spots=weak_spots,
            recommendations=recommendations,
            alerts=alerts,
            generated_date=date.today().strftime("%Y-%m-%d"),
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"class_report_{class_id}_{date.today().strftime('%Y%m%d')}.pdf"
    pdf_path = OUTPUT_DIR / pdf_filename

    await compile_tex_to_pdf(tex_source, pdf_path)

    return str(pdf_path)


async def list_class_reports(class_id: str) -> list[dict]:
    pattern = f"class_report_{class_id}_*.pdf"
    results = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.glob(pattern), reverse=True):
            results.append({
                "filename": f.name,
                "path": str(f),
                "class_id": class_id,
                "generated_date": f.stem.split("_")[-1],
            })
    return results
