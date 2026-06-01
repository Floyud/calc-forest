"""Homework analytics service — aggregated views for teachers."""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.db import get_db
from app.exceptions import NotFoundException

ERROR_LABELS: dict[str, str] = {
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
    "E99": "未识别错因",
    "OK": "正确",
}


DEMO_CLASS_HISTORY: list[dict[str, Any]] = [
    {
        "homework_id": "DEMO-0612",
        "created_at": "2026-05-12",
        "status": "graded",
        "problem_count": 6,
        "submission_count": 32,
        "avg_accuracy": 0.61,
        "top_error": "E05",
    },
    {
        "homework_id": "DEMO-0615",
        "created_at": "2026-05-15",
        "status": "graded",
        "problem_count": 6,
        "submission_count": 31,
        "avg_accuracy": 0.66,
        "top_error": "E06",
    },
    {
        "homework_id": "DEMO-0618",
        "created_at": "2026-05-18",
        "status": "graded",
        "problem_count": 8,
        "submission_count": 32,
        "avg_accuracy": 0.72,
        "top_error": "E10",
    },
    {
        "homework_id": "DEMO-0621",
        "created_at": "2026-05-21",
        "status": "graded",
        "problem_count": 6,
        "submission_count": 30,
        "avg_accuracy": 0.69,
        "top_error": "E05",
    },
    {
        "homework_id": "DEMO-0624",
        "created_at": "2026-05-24",
        "status": "graded",
        "problem_count": 8,
        "submission_count": 32,
        "avg_accuracy": 0.77,
        "top_error": "E09",
    },
]


def _demo_class_homework_history(class_id: str) -> dict[str, Any]:
    return {
        "class_id": class_id,
        "total_homeworks": 18,
        "avg_accuracy": 0.68,
        "completion_rate": 0.94,
        "most_common_error": "E05",
        "recent_homeworks": DEMO_CLASS_HISTORY,
        "error_distribution": {"E05": 24, "E06": 18, "E10": 15, "E09": 12},
        "demo_mode": True,
    }


def _is_sparse_class_history(history: dict[str, Any]) -> bool:
    if history["total_homeworks"] == 0:
        return True
    if history["avg_accuracy"] <= 0.05 and history["completion_rate"] <= 0.05:
        return True
    return any(
        item["submission_count"] == 0 or item["avg_accuracy"] <= 0
        for item in history["recent_homeworks"]
    )


async def get_class_homework_history(class_id: str, limit: int = 20) -> dict[str, Any]:
    """Return aggregated homework analytics for a class.

    Response shape matches the frontend ClassHomeworkAnalytics type:
    { class_id, total_homeworks, avg_accuracy, completion_rate,
      most_common_error, recent_homeworks, error_distribution }
    """
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cur.fetchone() is None:
            raise NotFoundException(f"班级 {class_id} 不存在")

        # --- batch query: homework list with aggregated answer stats ---
        cur = await db.execute(
            """SELECT hw.id, hw.status, hw.created_at,
                      hp_cnt.cnt AS problem_count,
                      COALESCE(sub_cnt.cnt, 0) AS submission_count,
                      COALESCE(sa_agg.total, 0) AS answer_total,
                      COALESCE(sa_agg.correct, 0) AS answer_correct
               FROM homework hw
               LEFT JOIN (SELECT homework_id, COUNT(*) AS cnt FROM homework_problems GROUP BY homework_id) hp_cnt
                 ON hp_cnt.homework_id = hw.id
               LEFT JOIN (SELECT homework_id, COUNT(*) AS cnt FROM homework_submissions GROUP BY homework_id) sub_cnt
                 ON sub_cnt.homework_id = hw.id
               LEFT JOIN (
                 SELECT homework_id,
                        COUNT(*) AS total,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct
                 FROM student_answers GROUP BY homework_id
               ) sa_agg ON sa_agg.homework_id = hw.id
               WHERE hw.class_id = ?
               ORDER BY hw.created_at DESC LIMIT ?""",
            (class_id, limit),
        )
        hw_rows = await cur.fetchall()

        # --- batch query: per-homework top error ---
        cur = await db.execute(
            """SELECT homework_id, error_code, COUNT(*) AS cnt
               FROM student_answers
               WHERE homework_id IN (SELECT id FROM homework WHERE class_id = ? ORDER BY created_at DESC LIMIT ?)
                 AND is_correct = 0 AND error_code IS NOT NULL
               GROUP BY homework_id, error_code""",
            (class_id, limit),
        )
        error_rows = await cur.fetchall()

        hw_errors: dict[str, list[dict]] = {}
        for r in error_rows:
            hid = r["homework_id"]
            if hid not in hw_errors:
                hw_errors[hid] = []
            hw_errors[hid].append({"code": r["error_code"], "count": r["cnt"]})

        # --- assemble ---
        recent_homeworks: list[dict[str, Any]] = []
        all_errors: Counter[str] = Counter()
        total_correct = 0
        total_answers = 0
        total_submissions = 0
        total_problems_possible = 0

        for hw in hw_rows:
            hid = hw["id"]
            p_cnt = hw["problem_count"] or 0
            s_cnt = hw["submission_count"] or 0
            a_total = hw["answer_total"] or 0
            a_correct = hw["answer_correct"] or 0
            acc = round(a_correct / a_total, 4) if a_total > 0 else 0.0

            errors = hw_errors.get(hid, [])
            top_error = errors[0]["code"] if errors else None

            for e in errors:
                all_errors[e["code"]] += e["count"]

            total_correct += a_correct
            total_answers += a_total
            total_submissions += s_cnt
            total_problems_possible += p_cnt * 10

            recent_homeworks.append({
                "homework_id": hid,
                "created_at": hw["created_at"],
                "status": hw["status"],
                "problem_count": p_cnt,
                "submission_count": s_cnt,
                "avg_accuracy": acc,
                "top_error": top_error,
            })

        avg_accuracy = round(total_correct / total_answers, 4) if total_answers > 0 else 0.0
        completion_rate = round(total_submissions / total_problems_possible, 4) if total_problems_possible > 0 else 0.0
        most_common = all_errors.most_common(1)[0][0] if all_errors else None

        history = {
            "class_id": class_id,
            "total_homeworks": len(hw_rows),
            "avg_accuracy": avg_accuracy,
            "completion_rate": completion_rate,
            "most_common_error": most_common,
            "recent_homeworks": recent_homeworks,
            "error_distribution": dict(all_errors),
        }
        return _demo_class_homework_history(class_id) if _is_sparse_class_history(history) else history


async def get_homework_detail_analytics(homework_id: str) -> dict[str, Any]:
    """Return detailed analytics for a single homework."""
    async with get_db() as db:
        hcur = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        hw = await hcur.fetchone()
        if hw is None:
            raise NotFoundException(f"作业 {homework_id} 不存在")

        pcur = await db.execute(
            "SELECT COUNT(*) as cnt FROM homework_problems WHERE homework_id = ?",
            (homework_id,),
        )
        problem_count = (await pcur.fetchone())["cnt"]

        scur = await db.execute(
            "SELECT COUNT(*) as cnt FROM homework_submissions WHERE homework_id = ?",
            (homework_id,),
        )
        submission_count = (await scur.fetchone())["cnt"]

        acur = await db.execute(
            """SELECT
                 COUNT(*) as total,
                 SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
               FROM student_answers WHERE homework_id = ?""",
            (homework_id,),
        )
        arow = await acur.fetchone()
        total = arow["total"] or 0
        correct = arow["correct"] or 0
        avg_accuracy = round(correct / total, 4) if total > 0 else 0.0

        ecur = await db.execute(
            """SELECT error_code, COUNT(*) as cnt FROM student_answers
               WHERE homework_id = ? AND is_correct = 0 AND error_code IS NOT NULL
               GROUP BY error_code ORDER BY cnt DESC""",
            (homework_id,),
        )
        error_distribution = [
            {"code": r["error_code"], "count": r["cnt"], "label": ERROR_LABELS.get(r["error_code"], r["error_code"])}
            for r in await ecur.fetchall()
        ]

        ppcur = await db.execute(
            """SELECT
                 sa.problem_sequence as sequence,
                 hp.target_error_code as error_code,
                 hp.difficulty as difficulty,
                 COUNT(*) as total,
                 SUM(CASE WHEN sa.is_correct = 1 THEN 1 ELSE 0 END) as correct
               FROM student_answers sa
               JOIN homework_problems hp ON sa.homework_id = hp.homework_id
                 AND sa.problem_sequence = hp.sequence
               WHERE sa.homework_id = ?
               GROUP BY sa.problem_sequence
               ORDER BY sa.problem_sequence""",
            (homework_id,),
        )
        per_problem_accuracy = [
            {
                "sequence": r["sequence"],
                "accuracy": round((r["correct"] or 0) / r["total"], 4) if r["total"] > 0 else 0.0,
                "error_code": r["error_code"],
                "difficulty": r["difficulty"],
            }
            for r in await ppcur.fetchall()
        ]

        srcur = await db.execute(
            """SELECT
                 sa.student_id,
                 s.name as student_name,
                 COUNT(*) as total_count,
                 SUM(CASE WHEN sa.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
               FROM student_answers sa
               JOIN students s ON sa.student_id = s.id
               WHERE sa.homework_id = ?
               GROUP BY sa.student_id
               ORDER BY sa.student_id""",
            (homework_id,),
        )
        student_rows = await srcur.fetchall()
        student_results: list[dict[str, Any]] = []
        needs_attention: list[str] = []

        # Batch: top error per student for this homework (single query)
        pecur = await db.execute(
            """SELECT student_id, error_code, cnt FROM (
                SELECT student_id, error_code, COUNT(*) as cnt,
                       ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY COUNT(*) DESC) as rn
                FROM student_answers
                WHERE homework_id = ? AND is_correct = 0 AND error_code IS NOT NULL
                GROUP BY student_id, error_code
               ) WHERE rn = 1""",
            (homework_id,),
        )
        primary_error_map: dict[str, str] = {}
        for pe_row in await pecur.fetchall():
            primary_error_map[pe_row["student_id"]] = pe_row["error_code"]

        for sr in student_rows:
            t = sr["total_count"]
            c = sr["correct_count"] or 0
            accuracy = round(c / t, 4) if t > 0 else 0.0
            primary_error = primary_error_map.get(sr["student_id"])

            student_results.append({
                "student_id": sr["student_id"],
                "student_name": sr["student_name"],
                "accuracy": accuracy,
                "correct_count": c,
                "total_count": t,
                "primary_error": primary_error,
                "review_status": "pending_teacher_review",
            })

            if accuracy < 0.5:
                needs_attention.append(sr["student_id"])

        accuracy_trend_vs_last = await _compute_accuracy_trend(db, hw["class_id"], homework_id, hw["created_at"])

        return {
            "homework_id": homework_id,
            "status": hw["status"],
            "problem_count": problem_count,
            "submission_count": submission_count,
            "avg_accuracy": avg_accuracy,
            "error_distribution": error_distribution,
            "per_problem_accuracy": per_problem_accuracy,
            "student_results": student_results,
            "needs_attention": needs_attention,
            "accuracy_trend_vs_last": accuracy_trend_vs_last,
        }


async def _compute_accuracy_trend(
    db: Any, class_id: str, homework_id: str, created_at: str
) -> float | None:
    prev_cur = await db.execute(
        """SELECT id FROM homework
           WHERE class_id = ? AND created_at < ? AND id != ?
           ORDER BY created_at DESC LIMIT 1""",
        (class_id, created_at, homework_id),
    )
    prev_hw = await prev_cur.fetchone()
    if prev_hw is None:
        return None

    cur_acc = await _hw_accuracy(db, homework_id)
    prev_acc = await _hw_accuracy(db, prev_hw["id"])

    if cur_acc is None or prev_acc is None:
        return None

    return round(cur_acc - prev_acc, 4)


async def _hw_accuracy(db: Any, homework_id: str) -> float | None:
    cur = await db.execute(
        """SELECT
             COUNT(*) as total,
             SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
           FROM student_answers WHERE homework_id = ?""",
        (homework_id,),
    )
    row = await cur.fetchone()
    total = row["total"] or 0
    correct = row["correct"] or 0
    if total == 0:
        return None
    return correct / total


async def get_student_homework_summary(student_id: str, limit: int = 10) -> dict[str, Any]:
    async with get_db() as db:
        scur = await db.execute("SELECT id, name FROM students WHERE id = ?", (student_id,))
        student = await scur.fetchone()
        if student is None:
            raise NotFoundException(f"学生 {student_id} 不存在")

        hwcur = await db.execute(
            """SELECT DISTINCT sa.homework_id, hw.created_at
               FROM student_answers sa
               JOIN homework hw ON sa.homework_id = hw.id
               WHERE sa.student_id = ?
               ORDER BY hw.created_at DESC
               LIMIT ?""",
            (student_id, limit),
        )
        hw_rows = await hwcur.fetchall()
        hw_ids = [hw["homework_id"] for hw in hw_rows]

        tcur = await db.execute(
            """SELECT COUNT(DISTINCT homework_id) as cnt FROM student_answers
               WHERE student_id = ?""",
            (student_id,),
        )
        total_homeworks = (await tcur.fetchone())["cnt"]

        # Batch: accuracy stats for all homework_ids
        acc_map: dict[str, dict[str, int]] = {}
        if hw_ids:
            placeholders = ",".join("?" for _ in hw_ids)
            acur = await db.execute(
                f"""SELECT homework_id,
                       COUNT(*) as total,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM student_answers
                   WHERE student_id = ? AND homework_id IN ({placeholders})
                   GROUP BY homework_id""",
                (student_id, *hw_ids),
            )
            for arow in await acur.fetchall():
                acc_map[arow["homework_id"]] = {
                    "total": arow["total"] or 0,
                    "correct": arow["correct"] or 0,
                }

        # Batch: top error per homework for this student
        pe_map: dict[str, str] = {}
        if hw_ids:
            placeholders = ",".join("?" for _ in hw_ids)
            pecur = await db.execute(
                f"""SELECT homework_id, error_code, cnt FROM (
                    SELECT homework_id, error_code, COUNT(*) as cnt,
                           ROW_NUMBER() OVER (PARTITION BY homework_id ORDER BY COUNT(*) DESC) as rn
                    FROM student_answers
                    WHERE student_id = ? AND homework_id IN ({placeholders})
                      AND is_correct = 0 AND error_code IS NOT NULL
                    GROUP BY homework_id, error_code
                   ) WHERE rn = 1""",
                (student_id, *hw_ids),
            )
            for pe_row in await pecur.fetchall():
                pe_map[pe_row["homework_id"]] = pe_row["error_code"]

        homework_history: list[dict[str, Any]] = []
        accuracies: list[float] = []

        for hw in hw_rows:
            hid = hw["homework_id"]
            stats = acc_map.get(hid, {"total": 0, "correct": 0})
            t = stats["total"]
            c = stats["correct"]
            accuracy = round(c / t, 4) if t > 0 else 0.0
            accuracies.append(accuracy)

            homework_history.append({
                "homework_id": hid,
                "accuracy": accuracy,
                "correct_count": c,
                "total_count": t,
                "primary_error": pe_map.get(hid),
                "created_at": hw["created_at"],
            })

        avg_accuracy = round(sum(accuracies) / len(accuracies), 4) if accuracies else 0.0

        recent_trend = "stable"
        if len(accuracies) >= 3:
            recent_avg = sum(accuracies[:3]) / 3
            prior_avg = sum(accuracies[3:6]) / 3 if len(accuracies) >= 6 else accuracies[-1]
            delta = recent_avg - prior_avg
            if delta > 0.05:
                recent_trend = "improving"
            elif delta < -0.05:
                recent_trend = "declining"
        elif len(accuracies) >= 2:
            delta = accuracies[0] - accuracies[-1]
            if delta > 0.05:
                recent_trend = "improving"
            elif delta < -0.05:
                recent_trend = "declining"

        return {
            "student_id": student_id,
            "total_homeworks": total_homeworks,
            "avg_accuracy": avg_accuracy,
            "recent_trend": recent_trend,
            "homework_history": homework_history,
        }
