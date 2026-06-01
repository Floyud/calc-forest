from __future__ import annotations

import json
import logging
import re
import uuid

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile

from app.schemas import (
    Homework,
    HomeworkGenerateRequest,
    HomeworkGradeResult,
    HomeworkLifecycleRequest,
    HomeworkSubmitRequest,
    SimulateRequest,
)

from app.exceptions import NotFoundException

logger = logging.getLogger(__name__)


def _extract_answer_from_baidu_reason(reason: str) -> str:
    """Extract the student's answer from Baidu slot reason text.

    Baidu format: "[PRESENCE: YES][TYPE: ...][NORM: xxx][ANS: yyy] ..."
    The NORM field contains the normalized answer text.
    """
    m = re.search(r'\[NORM:\s*([^\]]+)\]', reason)
    if m:
        return m.group(1).strip()
    m = re.search(r'\[ANS:\s*([^\]]+)\]', reason)
    if m:
        return m.group(1).strip()
    return ""

router = APIRouter(prefix="/api/homework", tags=["homework"])


@router.post("/generate", response_model=Homework)
async def homework_generate_endpoint(request: HomeworkGenerateRequest):
    from app.services.homework_service import generate_homework, validate_class_exists

    try:
        await validate_class_exists(request.class_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"班级 {request.class_id} 不存在")

    result = await generate_homework(
        class_id=request.class_id,
        grade=request.grade,
        student_id=request.student_id,
        error_codes_target=request.error_codes_target or None,
        problem_count=request.problem_count,
        difficulty=request.difficulty,
        exercise_types=request.exercise_types,
        difficulty_strategy=request.difficulty_strategy,
    )
    return result


@router.get("/{homework_id}", response_model=Homework)
async def homework_detail_endpoint(homework_id: str):
    from app.services.homework_service import get_homework

    homework = await get_homework(homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="作业不存在")
    return homework


@router.post("/assign")
async def homework_assign_endpoint(
    homework_id: str | None = None,
    class_id: str | None = None,
    due_date: str | None = None,
    body: dict | None = Body(default=None),
):
    from app.services.homework_service import assign_homework, get_homework
    if not homework_id and body:
        homework_id = body.get("homework_id")
    if not class_id and body:
        class_id = body.get("class_id")
    if not due_date and body:
        due_date = body.get("due_date")
    if not homework_id:
        raise HTTPException(status_code=400, detail="需要提供 homework_id")
    hw = await get_homework(homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="作业不存在")
    await assign_homework(homework_id, due_date)
    return {"homework_id": homework_id, "class_id": class_id, "status": "assigned"}


@router.post("/submit")
async def homework_submit_endpoint(request: HomeworkSubmitRequest):
    from app.services.grading_service import submit_homework
    result = await submit_homework(request.homework_id, request.student_id, request.answers)
    return result


@router.post("/grade", response_model=HomeworkGradeResult)
async def homework_grade_endpoint(homework_id: str, student_id: str):
    from app.services.grading_service import grade_homework
    result = await grade_homework(homework_id, student_id)
    return result


@router.post("/{homework_id}/generate-pdf")
async def homework_pdf_endpoint(
    homework_id: str,
    class_id: str,
    class_name: str = "",
    student_id: str | None = None,
    student_name: str | None = None,
    title: str = "课后练习",
):
    from app.services.pdf_service import generate_homework_pdf
    from fastapi.responses import FileResponse
    import os

    try:
        pdf_path = await generate_homework_pdf(
            homework_id=homework_id,
            class_id=class_id,
            class_name=class_name,
            student_id=student_id,
            student_name=student_name,
            title=title,
        )
        filename = os.path.basename(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{homework_id}/pdfs")
async def homework_pdf_list_endpoint(homework_id: str):
    from app.services.pdf_service import get_homework_pdf_paths
    return await get_homework_pdf_paths(homework_id)


@router.post("/batch-pipeline")
async def homework_batch_pipeline_endpoint(
    class_id: str = "G6C1",
    grade: int = 6,
    semester: int = 1,
    difficulty: str = "A",
    problem_count: int = 5,
    unit_title: str = "",
    use_llm: bool = False,
    teacher_id: str = "T001",
):
    from app.services.homework_service import generate_and_insert_homework
    from app.services.pdf_service import generate_homework_pdf

    hw = await generate_and_insert_homework(
        class_id=class_id, grade=grade, difficulty=difficulty,
        problem_count=problem_count, use_llm=use_llm,
        semester=semester, unit_title=unit_title,
    )

    try:
        pdf_path = await generate_homework_pdf(
            homework_id=hw["homework_id"],
            class_id=class_id,
            class_name=hw["class_name"],
            title=unit_title or "课后练习",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")

    return {
        "homework_id": hw["homework_id"],
        "class_id": class_id,
        "class_name": hw["class_name"],
        "problem_count": len(hw["raw_problems"]),
        "generated_by": hw["generated_by"],
        "pdf_path": pdf_path,
    }


@router.post("/batch-pipeline/class")
async def homework_batch_class_endpoint(
    class_id: str = Body("G6C1"),
    grade: int = Body(6),
    semester: int = Body(1),
    difficulty: str = Body("A"),
    problem_count: int = Body(5),
    unit_title: str = Body(""),
    title: str = Body("课后练习"),
    error_codes: list[str] = Body(["E01", "E02", "E03", "E04", "E05", "E07"]),
    use_llm: bool = Body(False),
):
    from app.services.homework_service import generate_and_insert_homework
    from app.services.pdf_service import batch_generate_pdfs

    hw = await generate_and_insert_homework(
        class_id=class_id, grade=grade, difficulty=difficulty,
        problem_count=problem_count, use_llm=use_llm,
        semester=semester, unit_title=unit_title,
        error_codes=error_codes,
    )

    pdf_paths = await batch_generate_pdfs(
        homework_id=hw["homework_id"],
        class_id=class_id,
        class_name=hw["class_name"],
        title=unit_title or "课后练习",
    )

    return {
        "homework_id": hw["homework_id"],
        "class_id": class_id,
        "class_name": hw["class_name"],
        "problem_count": len(hw["raw_problems"]),
        "pdf_count": len(pdf_paths),
        "pdf_paths": pdf_paths,
        "generated_by": hw["generated_by"],
    }


@router.post("/lifecycle")
async def homework_lifecycle(request: HomeworkLifecycleRequest):
    from app.services.homework_lifecycle import run_full_lifecycle

    return await run_full_lifecycle(
        class_id=request.class_id,
        grade=request.grade,
        problem_count=request.problem_count,
        error_codes=request.error_codes,
        difficulty=request.difficulty,
        unit_title=request.unit_title,
        use_llm=request.use_llm,
        simulate=request.simulate,
        ai_grade=request.ai_grade,
        ai_profile=request.ai_profile,
    )


@router.post("/{homework_id}/simulate")
async def simulate_answers(homework_id: str, request: SimulateRequest):
    from app.services.student_simulator import simulate_class_answers
    from app.services.grading_service import submit_homework

    sim = await simulate_class_answers(homework_id, request.class_id)
    submitted = {}
    for student_id, answers in sim["answers"].items():
        result = await submit_homework(homework_id, student_id, answers)
        submitted[student_id] = result
    return {
        "homework_id": homework_id,
        "simulation": sim["summary"],
        "submissions": submitted,
    }


@router.post("/{homework_id}/ai-grade")
async def ai_grade_homework_endpoint(homework_id: str, class_id: str = "G6C1"):
    from app.services.ai_grading_service import ai_grade_homework
    return await ai_grade_homework(homework_id, class_id)


@router.post("/{homework_id}/ai-profile")
async def ai_profile_homework_endpoint(homework_id: str, class_id: str = "G6C1"):
    from app.services.ai_profile_service import ai_update_profiles_after_grading
    return await ai_update_profiles_after_grading(homework_id)


@router.get("/class/{class_id}/analytics")
async def class_homework_analytics_endpoint(class_id: str, limit: int = 20):
    from app.services.homework_analytics import get_class_homework_history

    try:
        return await get_class_homework_history(class_id, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.get("/{homework_id}/analytics")
async def homework_analytics_endpoint(homework_id: str):
    from app.services.homework_analytics import get_homework_detail_analytics

    try:
        return await get_homework_detail_analytics(homework_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.get("/student/{student_id}/summary")
async def student_homework_summary_endpoint(student_id: str, limit: int = 10):
    from app.services.homework_analytics import get_student_homework_summary

    try:
        return await get_student_homework_summary(student_id, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.post("/{homework_id}/scan-grade")
async def scan_and_grade_endpoint(
    homework_id: str,
    file: UploadFile = File(...),
    student_id: str = Form(...),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    import os
    from app.db import get_db
    from app.services.grading_service import submit_homework, grade_homework

    async with get_db() as db:
        cur = await db.execute("SELECT id FROM homework WHERE id = ?", (homework_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "作业不存在")

        cur2 = await db.execute(
            "SELECT sequence, problem, correct_answer FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problems = [dict(r) for r in await cur2.fetchall()]

    if not problems:
        raise HTTPException(404, "该作业没有题目")

    image_bytes = await file.read()

    # ── OCR Phase: try Baidu first, fall back to local ──────────────
    baidu_api_key = os.getenv("BAIDU_OCR_API_KEY", "")
    baidu_secret = os.getenv("BAIDU_OCR_SECRET_KEY", "")
    baidu_configured = bool(baidu_api_key and baidu_secret)

    ocr_source = "local"
    answers: list[dict] = []
    baidu_result = None
    ocr_raw_json = ""

    if baidu_configured:
        try:
            from app.services.baidu_ocr_service import (
                configure,
                correct_homework,
                CORRECT_WRONG,
            )

            configure(baidu_api_key, baidu_secret)
            baidu_result = await correct_homework(image_bytes)
            ocr_source = "baidu"
            ocr_raw_json = json.dumps(
                {"task_id": baidu_result.task_id, "status": baidu_result.status},
                ensure_ascii=False,
            )

            all_questions = []
            for img in baidu_result.images:
                all_questions.extend(img.questions)

            for q in all_questions:
                # Baidu sequence is 0-based → our problem_sequence is 1-based
                problem_sequence = q.sequence + 1
                student_answer = ""

                if q.correct_result == CORRECT_WRONG:
                    for slot in q.slots:
                        if slot.reason:
                            extracted = _extract_answer_from_baidu_reason(slot.reason)
                            if extracted:
                                student_answer = extracted
                                break

                answers.append({
                    "problem_sequence": problem_sequence,
                    "raw_answer": student_answer or "?",
                })

            logger.info(
                "Baidu OCR: task_id=%s, questions=%d",
                baidu_result.task_id,
                len(all_questions),
            )

        except Exception as e:
            logger.warning("Baidu OCR failed (%s), falling back to local OCR", e)
            baidu_result = None

    if ocr_source == "local" or not answers:
        from app.services.ocr_service import recognize_work_image

        ocr_result = recognize_work_image(image_bytes)
        ocr_raw_json = ocr_result.text or ""

        all_texts = ocr_result.all_texts or [ocr_result.text] if ocr_result.text else []
        numbers = []
        for text in all_texts:
            for m in re.finditer(r"-?[\d]+(?:\.[\d]+)?(?:/[\d]+)?", text):
                val = m.group()
                try:
                    float(val.replace("/", "/"))
                    numbers.append(val)
                except ValueError:
                    pass

        answers = []
        for i, prob in enumerate(problems):
            if i < len(numbers):
                answers.append({"problem_sequence": prob["sequence"], "raw_answer": numbers[i]})

    if not answers:
        return {
            "homework_id": homework_id,
            "student_id": student_id,
            "status": "no_ocr_results",
            "recognized_count": 0,
            "total_problems": len(problems),
            "ocr_source": ocr_source,
            "results": [],
            "message": "未能识别出答案，请重新拍照或手动输入",
        }

    # ── Submit Phase ─────────────────────────────────────────────────
    await submit_homework(homework_id, student_id, answers)

    # ── Grade Phase (CRITICAL FIX: run diagnosis pipeline) ──────────
    try:
        grade_result = await grade_homework(homework_id, student_id)
    except Exception as e:
        logger.error("grade_homework failed after scan submit: %s", e)
        grade_result = {}

    # ── Audit: write to scanned_submissions ─────────────────────────
    scan_id = f"SCAN{uuid.uuid4().hex[:8].upper()}"
    try:
        async with get_db() as db:
            await db.execute(
                """INSERT INTO scanned_submissions
                   (id, student_id, homework_id, pdf_path, ocr_status, ocr_result_json, graded_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (scan_id, student_id, homework_id, "", "completed", ocr_raw_json, "graded"),
            )
            await db.commit()
    except Exception as e:
        logger.warning("Failed to insert scanned_submissions audit row: %s", e)

    # ── Query final answers (now populated with error_code/error_label) ─
    async with get_db() as db:
        cur3 = await db.execute(
            """SELECT sa.problem_sequence, sa.problem, sa.correct_answer, sa.student_answer,
                      sa.is_correct, sa.error_code, sa.error_label
               FROM student_answers sa
               WHERE sa.homework_id = ? AND sa.student_id = ?
               ORDER BY sa.problem_sequence""",
            (homework_id, student_id),
        )
        answer_rows = [dict(r) for r in await cur3.fetchall()]

    baidu_question_map: dict[int, dict] = {}
    if baidu_result:
        for img in baidu_result.images:
            for q in img.questions:
                seq = q.sequence + 1
                baidu_question_map[seq] = {
                    "baidu_question_type": q.question_type,
                    "baidu_crop_url": q.crop_url,
                    "baidu_slots": [
                        {
                            "slot_id": s.slot_id,
                            "sequence": s.sequence,
                            "correct_result": s.correct_result,
                            "reason": s.reason,
                        }
                        for s in q.slots
                    ],
                }

    ocr_texts_for_seq: dict[int, str] = {}
    if ocr_source == "local":
        all_texts_local = ocr_result.all_texts or [ocr_result.text] if ocr_result.text else []  # type: ignore[possibly-undefined]
        local_numbers: list[str] = []
        for text in all_texts_local:
            for m in re.finditer(r"-?[\d]+(?:\.[\d]+)?(?:/[\d]+)?", text):
                val = m.group()
                try:
                    float(val.replace("/", "/"))
                    local_numbers.append(val)
                except ValueError:
                    pass
        for i, prob in enumerate(problems):
            if i < len(local_numbers):
                ocr_texts_for_seq[prob["sequence"]] = local_numbers[i]

    results = []
    for r in answer_rows:
        item: dict = {
            "sequence": r["problem_sequence"],
            "problem": r["problem"],
            "correct_answer": r["correct_answer"],
            "student_answer": r["student_answer"],
            "recognized_text": ocr_texts_for_seq.get(r["problem_sequence"], ""),
            "is_correct": bool(r["is_correct"]),
            "error_code": r.get("error_code"),
            "error_label": r.get("error_label"),
            "baidu_question_type": None,
            "baidu_crop_url": None,
            "baidu_slots": None,
        }
        bq = baidu_question_map.get(r["problem_sequence"])
        if bq:
            item.update(bq)
        results.append(item)

    correct_count = sum(1 for r in results if r["is_correct"])
    recognized_count = len(answers)

    if recognized_count < len(problems):
        status = "partial"
    else:
        status = "graded"

    return {
        "homework_id": homework_id,
        "student_id": student_id,
        "status": status,
        "recognized_count": recognized_count,
        "total_problems": len(problems),
        "ocr_source": ocr_source,
        "results": results,
        "grading_summary": {
            "total": len(problems),
            "correct": correct_count,
            "accuracy": round(correct_count / max(len(problems), 1), 4),
        },
    }
