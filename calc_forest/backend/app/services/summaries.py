from __future__ import annotations

from collections import Counter

from app.db import get_db
from app.schemas import DiagnosisResponse


def summarize_class(diagnoses: list[DiagnosisResponse]) -> dict:
    counts = Counter(item.primary_error.code.value for item in diagnoses if not item.is_correct)
    return {
        "attempt_count": len(diagnoses),
        "top_error_tags": [{"code": code, "count": count} for code, count in counts.most_common(5)],
        "teacher_brief": "优先讲评出现次数最高的错因，所有建议需教师审核后使用。",
    }


async def get_class_error_summary(class_id: str) -> dict:
    """DB-backed class error summary with student tiers."""
    async with get_db() as db:
        cur = await db.execute("SELECT name, student_ids FROM classes WHERE id = ?", (class_id,))
        cls_row = await cur.fetchone()
        if cls_row is None:
            return None

        cur = await db.execute("SELECT COUNT(*) FROM students WHERE class_id = ?", (class_id,))
        total_students = (await cur.fetchone())[0]

        cur = await db.execute(
            """SELECT ses.student_id, ses.error_code,
                      ses.total_attempts, ses.correct_count
               FROM student_error_stats ses
               JOIN students s ON s.id = ses.student_id
               WHERE s.class_id = ?""",
            (class_id,),
        )
        stats_rows = await cur.fetchall()

        if not stats_rows:
            return {
                "class_id": class_id,
                "class_name": cls_row["name"],
                "total_students": total_students,
                "class_accuracy": 0.0,
                "error_distribution": [],
                "student_tiers": {"优秀": [], "良好": [], "需关注": []},
                "review_status": "pending_teacher_review",
            }

        total_attempts = sum(r["total_attempts"] for r in stats_rows)
        total_correct = sum(r["correct_count"] for r in stats_rows)
        class_accuracy = round(total_correct / total_attempts, 4) if total_attempts else 0.0

        error_counter = Counter()
        for r in stats_rows:
            if r["error_code"] != "OK":
                error_counter[r["error_code"]] += r["total_attempts"] - r["correct_count"]
        error_distribution = [
            {"code": code, "count": count}
            for code, count in error_counter.most_common(5)
        ]

        student_agg: dict[str, dict] = {}
        for r in stats_rows:
            sid = r["student_id"]
            if sid not in student_agg:
                student_agg[sid] = {"total": 0, "correct": 0}
            student_agg[sid]["total"] += r["total_attempts"]
            student_agg[sid]["correct"] += r["correct_count"]

        tiers: dict[str, list[str]] = {"优秀": [], "良好": [], "需关注": []}
        for sid, agg in student_agg.items():
            acc = agg["correct"] / agg["total"] if agg["total"] else 0.0
            if acc >= 0.85:
                tiers["优秀"].append(sid)
            elif acc >= 0.7:
                tiers["良好"].append(sid)
            else:
                tiers["需关注"].append(sid)

    return {
        "class_id": class_id,
        "class_name": cls_row["name"],
        "total_students": total_students,
        "total_attempts": total_attempts,
        "class_accuracy": class_accuracy,
        "error_distribution": error_distribution,
        "student_tiers": tiers,
        "review_status": "pending_teacher_review",
    }


async def get_class_period_summary(class_id: str, period: str = "weekly") -> dict:
    """Weekly/monthly accuracy trend for a class."""
    async with get_db() as db:
        cur = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        cls_row = await cur.fetchone()
        if cls_row is None:
            return None

        if period == "monthly":
            date_expr = "strftime('%Y-%m', dh.created_at)"
        else:
            date_expr = "strftime('%Y-W%W', dh.created_at)"

        cur = await db.execute(
            f"""SELECT {date_expr} AS period_label,
                       COUNT(*) AS attempt_count,
                       SUM(dh.is_correct) AS correct_count
                FROM diagnosis_history dh
                JOIN students s ON s.id = dh.student_id
                WHERE s.class_id = ?
                GROUP BY period_label
                ORDER BY period_label""",
            (class_id,),
        )
        trend_rows = await cur.fetchall()

        sa_date_expr = "strftime('%Y-%m', sa.created_at)" if period == "monthly" else "strftime('%Y-W%W', sa.created_at)"
        cur2 = await db.execute(
            f"""SELECT {sa_date_expr} AS period_label,
                       COUNT(*) AS attempt_count,
                       SUM(sa.is_correct) AS correct_count
                FROM student_answers sa
                JOIN students s ON s.id = sa.student_id
                WHERE s.class_id = ?
                GROUP BY period_label
                ORDER BY period_label""",
            (class_id,),
        )
        sa_trend_rows = await cur2.fetchall()

        merged: dict[str, dict] = {}
        for r in trend_rows:
            pl = r["period_label"]
            if pl not in merged:
                merged[pl] = {"attempts": 0, "correct": 0}
            merged[pl]["attempts"] += r["attempt_count"]
            merged[pl]["correct"] += r["correct_count"]

        for r in sa_trend_rows:
            pl = r["period_label"]
            if pl not in merged:
                merged[pl] = {"attempts": 0, "correct": 0}
            merged[pl]["attempts"] += r["attempt_count"]
            merged[pl]["correct"] += r["correct_count"]

        accuracy_trend = [
            {
                "period_label": pl,
                "accuracy": round(v["correct"] / v["attempts"], 4) if v["attempts"] else 0.0,
                "attempt_count": v["attempts"],
            }
            for pl, v in sorted(merged.items())
        ]

        cur = await db.execute(
            """SELECT ses.student_id, s.name,
                      SUM(ses.total_attempts) AS total_attempts,
                      SUM(ses.correct_count) AS correct_count
               FROM student_error_stats ses
               JOIN students s ON s.id = ses.student_id
               WHERE s.class_id = ?
               GROUP BY ses.student_id""",
            (class_id,),
        )
        student_rows = await cur.fetchall()

        most_improved = None
        needs_attention: list[dict] = []

        if len(accuracy_trend) >= 2:
            cur = await db.execute(
                """SELECT dh.student_id, s.name,
                          {date_expr} AS period_label,
                          COUNT(*) AS attempt_count,
                          SUM(dh.is_correct) AS correct_count
                   FROM diagnosis_history dh
                   JOIN students s ON s.id = dh.student_id
                   WHERE s.class_id = ?
                   GROUP BY dh.student_id, period_label
                   ORDER BY dh.student_id, period_label""".format(date_expr=date_expr),
                (class_id,),
            )
            per_student_trend = await cur.fetchall()

            student_periods: dict[str, list] = {}
            for r in per_student_trend:
                sid = r["student_id"]
                if sid not in student_periods:
                    student_periods[sid] = {"name": r["name"], "periods": []}
                acc = r["correct_count"] / r["attempt_count"] if r["attempt_count"] else 0.0
                student_periods[sid]["periods"].append(acc)

            best_improvement = -999.0
            for sid, data in student_periods.items():
                periods = data["periods"]
                if len(periods) >= 2:
                    first = periods[0]
                    last = periods[-1]
                    change = last - first
                    if change > best_improvement:
                        best_improvement = change
                        most_improved = {
                            "student_id": sid,
                            "name": data["name"],
                            "accuracy_change": round(change, 4),
                        }
                    if change < 0:
                        needs_attention.append({
                            "student_id": sid,
                            "name": data["name"],
                            "accuracy_change": round(change, 4),
                        })

    return {
        "class_id": class_id,
        "class_name": cls_row["name"],
        "period": period,
        "accuracy_trend": accuracy_trend,
        "most_improved": most_improved,
        "needs_attention": needs_attention,
        "review_status": "pending_teacher_review",
    }


async def get_error_code_breakdown(class_id: str) -> dict:
    """Detailed per-error-code analysis for a class."""
    async with get_db() as db:
        cur = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        cls_row = await cur.fetchone()
        if cls_row is None:
            return None

        cur = await db.execute(
            """SELECT ses.error_code,
                      SUM(ses.total_attempts) AS total_occurrences,
                      SUM(ses.correct_count) AS total_correct,
                      COUNT(DISTINCT ses.student_id) AS affected_students
               FROM student_error_stats ses
               JOIN students s ON s.id = ses.student_id
               WHERE s.class_id = ? AND ses.error_code != 'OK'
               GROUP BY ses.error_code
               HAVING total_occurrences > 0
               ORDER BY total_occurrences DESC""",
            (class_id,),
        )
        rows = await cur.fetchall()

        error_codes = [
            {
                "code": r["error_code"],
                "total_occurrences": r["total_occurrences"],
                "affected_students": r["affected_students"],
                "avg_accuracy_for_code": round(
                    r["total_correct"] / r["total_occurrences"], 4
                ) if r["total_occurrences"] else 0.0,
            }
            for r in rows
        ]

    return {
        "class_id": class_id,
        "class_name": cls_row["name"],
        "error_codes": error_codes,
        "review_status": "pending_teacher_review",
    }
