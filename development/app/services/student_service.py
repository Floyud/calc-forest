from __future__ import annotations

import uuid
from collections import Counter

from app.db import get_db
from app.schemas import Student, StudentProfile

# Error code labels for guidance context
ERROR_LABELS = {
    "E01": "基础事实",
    "E02": "进位错误",
    "E03": "退位错误",
    "E04": "数位对齐",
    "E05": "运算顺序",
    "E06": "小数点/分数单位",
    "E07": "抄写转写",
    "E08": "步骤遗漏",
    "E09": "算理理解",
    "E10": "审题",
    "E11": "未验算",
}

# Chinese labels for mastery zones
ZONE_LABELS = {
    "mastered": "已掌握",
    "learning": "学习中",
    "needs_practice": "需练习",
    "no_data": "无数据",
}

# Trend labels
TREND_LABELS = {
    "improving": "进步中",
    "declining": "退步中",
    "stable": "稳定",
}


def _row_to_student(row) -> Student:
    import json

    return Student(
        student_id=row["id"],
        name=row["name"],
        grade=row["grade"],
        class_id=row["class_id"],
        student_number=row["student_number"] if "student_number" in row.keys() else "",
        guidance_mode=row["guidance_mode"],
        textbook_version=row["textbook_version"],
        start_grade=row["start_grade"],
        enrolled_at=row["enrolled_at"],
        personality_tags=json.loads(row["personality_tags"]) if "personality_tags" in row.keys() and row["personality_tags"] else [],
        learning_style=row["learning_style"] if "learning_style" in row.keys() else "",
        notes=row["notes"] if "notes" in row.keys() else "",
    )


async def get_student(student_id: str) -> Student | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_student(row)


async def list_students(class_id: str | None = None) -> list[Student]:
    async with get_db() as db:
        if class_id:
            cursor = await db.execute(
                "SELECT * FROM students WHERE class_id = ?", (class_id,)
            )
        else:
            cursor = await db.execute("SELECT * FROM students")
        rows = await cursor.fetchall()
    return [_row_to_student(r) for r in rows]


async def update_error_stats(
    student_id: str, error_code: str, is_correct: bool
) -> None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ? AND error_code = ?",
            (student_id, error_code),
        )
        row = await cursor.fetchone()

        if row:
            await db.execute(
                """UPDATE student_error_stats
                   SET total_attempts = total_attempts + 1,
                       correct_count = correct_count + ?,
                       last_seen_at = datetime('now')
                   WHERE id = ?""",
                (1 if is_correct else 0, row["id"]),
            )
        else:
            stat_id = f"SES{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO student_error_stats
                   (id, student_id, error_code, total_attempts, correct_count, last_seen_at)
                   VALUES (?, ?, ?, 1, ?, datetime('now'))""",
                (stat_id, student_id, error_code, 1 if is_correct else 0),
            )
        await db.commit()


async def batch_update_error_stats(
    student_id: str, results: list[tuple[str, bool]]
) -> None:
    """Batch-update error stats in a single DB connection.

    Args:
        student_id: The student ID.
        results: List of (error_code, is_correct) tuples.
    """
    if not results:
        return
    async with get_db() as db:
        for error_code, is_correct in results:
            await db.execute(
                """INSERT INTO student_error_stats
                       (id, student_id, error_code, total_attempts, correct_count, last_seen_at)
                       VALUES (?, ?, ?, 1, ?, datetime('now'))
                       ON CONFLICT(student_id, error_code) DO UPDATE SET
                       total_attempts = total_attempts + 1,
                       correct_count = correct_count + ?,
                       last_seen_at = datetime('now')""",
                (
                    f"SES{uuid.uuid4().hex[:8].upper()}",
                    student_id,
                    error_code,
                    1 if is_correct else 0,
                    1 if is_correct else 0,
                ),
            )
        await db.commit()


async def get_weak_knowledge_points(student_id: str) -> list[dict]:
    """
    Returns weak knowledge points for a student, ordered by accuracy (worst first).
    Each entry includes: error_code, unit_id, unit_title, knowledge_point,
    typical_error, accuracy, total_attempts, mastery_zone.
    Gracefully returns [] if error_code_knowledge_map table doesn't exist.
    """
    async with get_db() as db:
        try:
            cursor = await db.execute("""
                SELECT
                    eckm.error_code,
                    eckm.unit_title,
                    eckm.knowledge_point,
                    eckm.typical_error,
                    eckm.unit_id,
                    ses.total_attempts,
                    ses.correct_count,
                    CASE WHEN ses.total_attempts > 0
                        THEN CAST(ses.correct_count AS FLOAT) / ses.total_attempts
                        ELSE NULL END as accuracy
                FROM error_code_knowledge_map eckm
                LEFT JOIN student_error_stats ses
                    ON eckm.error_code = ses.error_code AND ses.student_id = ?
                WHERE eckm.error_code != 'OK'
                ORDER BY accuracy ASC, ses.total_attempts DESC
            """, (student_id,))
            rows = await cursor.fetchall()
        except Exception:
            # Table doesn't exist yet (parallel task creates it)
            return []

    results = []
    for row in rows:
        acc = row["accuracy"]
        if acc is None:
            zone = "no_data"
        elif acc >= 0.85:
            continue  # skip mastered error codes
        elif acc >= 0.5:
            zone = "learning"
        else:
            zone = "needs_practice"

        results.append({
            "error_code": row["error_code"],
            "unit_id": row["unit_id"],
            "unit_title": row["unit_title"],
            "knowledge_point": row["knowledge_point"],
            "typical_error": row["typical_error"],
            "accuracy": round(acc, 2) if acc is not None else None,
            "total_attempts": row["total_attempts"] or 0,
            "mastery_zone": zone,
        })

    # Deduplicate: keep best entry per error_code (lowest accuracy = weakest)
    seen: dict[str, dict] = {}
    for r in results:
        code = r["error_code"]
        if code not in seen or (
            r["accuracy"] is not None
            and (seen[code]["accuracy"] is None or r["accuracy"] < seen[code]["accuracy"])
        ):
            seen[code] = r

    return sorted(seen.values(), key=lambda x: x["accuracy"] if x["accuracy"] is not None else 1.0)


async def get_class_weak_points(class_id: str) -> list[dict]:
    """
    Aggregates weak knowledge points across all students in a class.
    Returns entries ordered by class-wide accuracy (worst first).
    Gracefully returns [] if error_code_knowledge_map table doesn't exist.
    """
    async with get_db() as db:
        try:
            cursor = await db.execute("""
                SELECT
                    eckm.error_code,
                    eckm.unit_title,
                    eckm.unit_id,
                    eckm.knowledge_point,
                    eckm.typical_error,
                    SUM(ses.total_attempts) AS total_attempts,
                    SUM(ses.correct_count) AS correct_count,
                    COUNT(DISTINCT ses.student_id) AS affected_students,
                    CASE WHEN SUM(ses.total_attempts) > 0
                        THEN CAST(SUM(ses.correct_count) AS FLOAT) / SUM(ses.total_attempts)
                        ELSE NULL END as accuracy
                FROM error_code_knowledge_map eckm
                LEFT JOIN student_error_stats ses
                    ON eckm.error_code = ses.error_code
                LEFT JOIN students s ON s.id = ses.student_id AND s.class_id = ?
                WHERE eckm.error_code != 'OK'
                GROUP BY eckm.error_code, eckm.unit_title, eckm.unit_id,
                         eckm.knowledge_point, eckm.typical_error
                ORDER BY accuracy ASC, total_attempts DESC
            """, (class_id,))
            rows = await cursor.fetchall()
        except Exception:
            return []

    results = []
    for row in rows:
        acc = row["accuracy"]
        if acc is None:
            zone = "no_data"
        elif acc >= 0.85:
            continue  # skip mastered error codes
        elif acc >= 0.5:
            zone = "learning"
        else:
            zone = "needs_practice"

        results.append({
            "error_code": row["error_code"],
            "unit_id": row["unit_id"],
            "unit_title": row["unit_title"],
            "knowledge_point": row["knowledge_point"],
            "typical_error": row["typical_error"],
            "accuracy": round(acc, 2) if acc is not None else None,
            "total_attempts": row["total_attempts"] or 0,
            "affected_students": row["affected_students"] or 0,
            "mastery_zone": zone,
        })

    # Deduplicate: keep best entry per error_code
    seen: dict[str, dict] = {}
    for r in results:
        code = r["error_code"]
        if code not in seen or (
            r["accuracy"] is not None
            and (seen[code]["accuracy"] is None or r["accuracy"] < seen[code]["accuracy"])
        ):
            seen[code] = r

    return sorted(seen.values(), key=lambda x: x["accuracy"] if x["accuracy"] is not None else 1.0)


async def get_error_code_accuracy(student_id: str) -> dict[str, float]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT error_code, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ?",
            (student_id,),
        )
        rows = await cursor.fetchall()

    result: dict[str, float] = {}
    for r in rows:
        if r["total_attempts"] > 0:
            result[r["error_code"]] = round(r["correct_count"] / r["total_attempts"], 4)
    return result


async def get_student_profile(student_id: str) -> StudentProfile | None:
    from app.schemas import WeeklyAccuracy

    async with get_db() as db:
        s_cursor = await db.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        s_row = await s_cursor.fetchone()
        if s_row is None:
            return None
        student = _row_to_student(s_row)

        dh_cursor = await db.execute(
            "SELECT is_correct, error_code, created_at FROM diagnosis_history "
            "WHERE student_id = ? ORDER BY created_at ASC",
            (student_id,),
        )
        dh_rows = list(await dh_cursor.fetchall())

        sa_cursor = await db.execute(
            "SELECT is_correct, error_code FROM student_answers "
            "WHERE student_id = ?",
            (student_id,),
        )
        sa_rows = list(await sa_cursor.fetchall())
        rows = dh_rows + sa_rows

        ses_cursor = await db.execute(
            "SELECT error_code, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ?",
            (student_id,),
        )
        ses_rows = await ses_cursor.fetchall()

    accuracy_by_error_code: dict[str, float] = {}
    for r in ses_rows:
        if r["total_attempts"] > 0:
            accuracy_by_error_code[r["error_code"]] = round(r["correct_count"] / r["total_attempts"], 4)

    total_attempts = len(rows)
    if total_attempts == 0:
        return StudentProfile(
            student_id=student_id,
            student=student,
        )

    correct_count = sum(1 for r in rows if r["is_correct"])
    accuracy = round(correct_count / total_attempts, 4)

    error_counter = Counter(
        r["error_code"] for r in rows if r["error_code"] != "OK"
    )
    dominant_error_tags = [code for code, _ in error_counter.most_common(3)]

    recent_accuracy_trend = "stable"
    if total_attempts >= 10:
        first5 = rows[:5]
        last5 = rows[-5:]
        first_acc = sum(1 for r in first5 if r["is_correct"]) / 5
        last_acc = sum(1 for r in last5 if r["is_correct"]) / 5
        diff = last_acc - first_acc
        if diff > 0.1:
            recent_accuracy_trend = "improving"
        elif diff < -0.1:
            recent_accuracy_trend = "declining"

    last_active_date = dh_rows[-1]["created_at"] if dh_rows else None

    weekly_accuracy: list[WeeklyAccuracy] = []
    weekly_group: dict[int, list[bool]] = {}
    for r in dh_rows:
        created = r["created_at"] or ""
        try:
            month = int(created[5:7]) if len(created) >= 7 else 0
        except (ValueError, IndexError):
            month = 0
        if month > 0:
            weekly_group.setdefault(month, []).append(bool(r["is_correct"]))

    for wk in sorted(weekly_group.keys()):
        attempts_list = weekly_group[wk]
        wk_total = len(attempts_list)
        wk_correct = sum(1 for x in attempts_list if x)
        weekly_accuracy.append(WeeklyAccuracy(
            week_number=wk,
            accuracy=round(wk_correct / wk_total, 4) if wk_total > 0 else 0.0,
            total_attempts=wk_total,
            correct_count=wk_correct,
        ))

    profile = StudentProfile(
        student_id=student_id,
        student=student,
        total_attempts=total_attempts,
        correct_count=correct_count,
        accuracy=accuracy,
        dominant_error_tags=dominant_error_tags,
        accuracy_by_error_code=accuracy_by_error_code,
        weak_knowledge_points=await get_weak_knowledge_points(student_id),
        weekly_accuracy=weekly_accuracy,
        recent_accuracy_trend=recent_accuracy_trend,
        last_active_date=last_active_date,
    )

    try:
        from app.services.growth_milestone import get_growth_milestone
        milestone = await get_growth_milestone(student_id)
        profile.growth_milestone = milestone
    except Exception:
        pass

    return profile


async def build_guidance_context(student_id: str) -> str:
    student = await get_student(student_id)
    if student is None:
        return f"未找到学生（ID: {student_id}）"

    profile = await get_student_profile(student_id)
    if profile is None:
        return f"学生 {student.name} 暂无学习数据。"

    from app.services.mastery_service import get_student_mastery
    mastery_data = await get_student_mastery(student_id)
    if "error" in mastery_data:
        mastery_error_codes: dict[str, dict] = {}
    else:
        mastery_error_codes = mastery_data.get("error_codes", {})

    accuracy = profile.accuracy or 0.0
    trend_label = TREND_LABELS.get(profile.recent_accuracy_trend or "stable", "稳定")

    tags = ", ".join(student.personality_tags) if student.personality_tags else ""
    learning_style = student.learning_style or ""

    header = (
        f"【学生学习画像】\n"
        f"学生：{student.name}（学号 {student.student_number}）| "
        f"六年级 | {student.class_id}班\n"
        f"总体正确率：{accuracy:.0%} | 近期趋势：{trend_label}"
    )
    if tags:
        header += f"\n学习特点：{tags}"
    if learning_style:
        header += f"\n学习风格：{learning_style}"

    sorted_codes = sorted(
        [(c, a) for c, a in profile.accuracy_by_error_code.items() if c != "OK"],
        key=lambda x: x[1],
    )

    mastery_lines: list[str] = ["\n【各错因掌握度】"]
    for code, acc in sorted_codes:
        label = ERROR_LABELS.get(code, code)
        mastery_info = mastery_error_codes.get(code, {})
        mastery_prob = mastery_info.get("mastery_probability", 0.0)
        zone = mastery_info.get("zone", "no_data")
        zone_label = ZONE_LABELS.get(zone, zone)

        if acc < 0.3:
            emoji = "🔴"
        elif acc < 0.6:
            emoji = "🟡"
        else:
            emoji = "🟢"

        mastery_lines.append(
            f"{emoji} {code} {label}: {acc:.0%} 正确率, "
            f"掌握度={mastery_prob:.0%} ({zone_label})"
        )

    weak_lines: list[str] = ["\n【薄弱知识点】"]
    weak_points = profile.weak_knowledge_points or []
    for wp in weak_points[:5]:
        code = wp.get("error_code", "")
        unit_title = wp.get("unit_title", "")
        kp = wp.get("knowledge_point", "")
        typical = wp.get("typical_error", "")
        line = f"{code} {unit_title}· {kp}"
        if typical:
            line += f" — 典型错误：{typical}"
        weak_lines.append(line)

    guidance_lines: list[str] = ["\n【引导建议】"]
    critical = [c for c, a in sorted_codes if a < 0.3]
    needs_work = [c for c, a in sorted_codes if 0.3 <= a < 0.6]

    if critical:
        code = critical[0]
        label = ERROR_LABELS.get(code, code)
        guidance_lines.append(
            f"- 学生{code}（{label}）极其薄弱，优先引导相关概念的位值理解"
        )
    if len(critical) > 1 or len(needs_work) > 0:
        all_weak = critical[1:] + needs_work[:2]
        for code in all_weak[:2]:
            label = ERROR_LABELS.get(code, code)
            guidance_lines.append(
                f"- {code}（{label}）多次出错，引导时强调分步验证"
            )

    if trend_label == "进步中" and critical:
        guidance_lines.append(
            f"- 学生近期有进步趋势，适当给予肯定"
        )

    sections = [header] + mastery_lines + weak_lines + guidance_lines
    result = "\n".join(sections)

    if len(result) > 2000:
        result = result[:1997] + "..."

    return result
