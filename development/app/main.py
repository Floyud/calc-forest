from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.params import Body
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db, close_db
from app.schemas import (
    AcademicCycle,
    Class,
    ClassForestResponse,
    ClassSummary,
    DifySessionDraftRequest,
    DifySessionDraftResponse,
    DiagnosisRequest,
    DiagnosisResponse,
    EncouragementRule,
    HealthResponse,
    HomeworkGenerateRequest,
    Homework,
    HomeworkGradeResult,
    HomeworkLifecycleRequest,
    HomeworkSubmitRequest,
    OCRTaskResponse,
    OCRUploadRequest,
    PracticeRecommendationRequest,
    PracticeRecommendationResponse,
    QuizGenerateRequest,
    QuizResponse,
    QuizResponseRecord,
    QuizSummary,
    SimulateRequest,
    Student,
    StudentCycleProgress,
    StudentProfile,
    Teacher,
    TeacherLoginRequest,
    TeacherLoginResponse,
    TreeSpecies,
)
from app.services.class_service import get_class as svc_get_class
from app.services.class_service import get_class_summary
from app.services.cycle_service import get_current_cycle, get_student_growth
from app.services.curriculum_service import (
    get_calendar,
    get_schedule,
    get_student_trajectory,
    get_units,
    update_student_profile,
    update_schedule,
)
from app.services.diagnosis import diagnose_answer
from app.services.growth import list_encouragement_rules, list_tree_species
from app.services.practice import recommend_practice
from app.services.session_draft import build_session_draft
from app.services.student_service import get_student as svc_get_student
from app.services.student_service import get_student_profile


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    from app.services.knowledge_service import init_knowledge_index

    await init_knowledge_index()
    yield
    from app.services.llm_client import llm_config
    await llm_config.close()
    await close_db()


app = FastAPI(
    title="My Calc Forest Tool API",
    version="0.1.0",
    description="Dify-first tool API for 我的计算森林.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3002", "http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/api/auth/login", response_model=TeacherLoginResponse)
async def teacher_login(request: TeacherLoginRequest):
    import json
    import secrets
    from app.db import get_db

    async with get_db() as db:
        if request.teacher_id:
            cur = await db.execute("SELECT * FROM teachers WHERE id = ?", (request.teacher_id,))
        elif request.phone:
            cur = await db.execute("SELECT * FROM teachers WHERE phone = ?", (request.phone,))
        else:
            cur = await db.execute("SELECT * FROM teachers LIMIT 1")

        row = await cur.fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="教师不存在")

        teacher = Teacher(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            avatar=row["avatar"],
            class_ids=json.loads(row["class_ids"]),
            created_at=row["created_at"],
        )

        class_ids = json.loads(row["class_ids"])
        classes = []
        for cid in class_ids:
            cur = await db.execute("SELECT * FROM classes WHERE id = ?", (cid,))
            c = await cur.fetchone()
            if c:
                classes.append(Class(
                    id=c["id"], name=c["name"], grade=c["grade"],
                    academic_year=c["academic_year"], semester=c["semester"],
                    student_ids=json.loads(c["student_ids"]),
                ))

    token = f"dev-token-{secrets.token_hex(8)}"
    return TeacherLoginResponse(teacher=teacher, token=token, classes=classes)


@app.get("/api/auth/me", response_model=Teacher)
async def get_current_teacher(teacher_id: str = "T001"):
    import json
    from app.db import get_db

    async with get_db() as db:
        cur = await db.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
        row = await cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="教师不存在")
        return Teacher(
            id=row["id"], name=row["name"], phone=row["phone"],
            avatar=row["avatar"], class_ids=json.loads(row["class_ids"]),
            created_at=row["created_at"],
        )


@app.get("/api/classes/{class_id}/forest", response_model=ClassForestResponse)
async def get_class_forest_endpoint(class_id: str):
    from app.services.forest_service import get_class_forest
    forest = await get_class_forest(class_id)
    if forest is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return forest


@app.post("/api/diagnose", response_model=DiagnosisResponse)
def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
    return diagnose_answer(request)


@app.post("/api/practice/recommend", response_model=PracticeRecommendationResponse)
def practice_recommend(
    request: PracticeRecommendationRequest,
) -> PracticeRecommendationResponse:
    return recommend_practice(request.error_code, request.grade, request.guidance_mode)


@app.get("/api/tree-species", response_model=list[TreeSpecies])
def tree_species() -> list[TreeSpecies]:
    return list_tree_species()


@app.get("/api/encouragements", response_model=list[EncouragementRule])
def encouragements() -> list[EncouragementRule]:
    return list_encouragement_rules()


@app.post("/api/dify/session-draft", response_model=DifySessionDraftResponse)
def dify_session_draft(request: DifySessionDraftRequest) -> DifySessionDraftResponse:
    return build_session_draft(request)


@app.post("/api/dify/full-pipeline", response_model=DifySessionDraftResponse)
async def full_pipeline_endpoint(request: DifySessionDraftRequest) -> DifySessionDraftResponse:
    from app.pipeline.session_draft_pipeline import create_full_pipeline
    from app.pipeline.response_assembler import assemble_response
    from app.schemas import AnswerRecord

    student_steps = []
    if request.student_steps_text:
        student_steps = [line.strip() for line in request.student_steps_text.splitlines() if line.strip()]

    record = AnswerRecord(
        student_id=request.student_id,
        grade=request.grade,
        problem=request.problem_text,
        correct_answer=request.correct_answer_text,
        student_answer=request.student_answer_text,
        student_steps=student_steps,
        source=request.source,
    )

    pipeline = create_full_pipeline()
    context = await pipeline.run({
        "record": record,
        "student_id": request.student_id,
        "grade": request.grade,
        "guidance_mode": request.guidance_mode,
        "class_id": None,
        "tree_species_id": request.tree_species_id,
        "problem": request.problem_text,
        "correct_answer": request.correct_answer_text,
        "student_answer": request.student_answer_text,
    })

    return assemble_response(context, request)


@app.get("/api/students/{student_id}", response_model=Student)
async def get_student_endpoint(student_id: str):
    student = await svc_get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.get("/api/students/{student_id}/profile", response_model=StudentProfile)
async def get_student_profile_endpoint(student_id: str):
    profile = await get_student_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return profile


@app.get("/api/classes/{class_id}", response_model=Class)
async def get_class_endpoint(class_id: str):
    cls = await svc_get_class(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


@app.get("/api/classes/{class_id}/summary", response_model=ClassSummary)
async def get_class_summary_endpoint(class_id: str):
    summary = await get_class_summary(class_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return summary


@app.get("/api/cycles/current", response_model=AcademicCycle)
async def get_current_cycle_endpoint(grade: int = 6):
    cycle = await get_current_cycle(grade)
    if cycle is None:
        raise HTTPException(status_code=404, detail="No current cycle found for this grade")
    return cycle


@app.get("/api/students/{student_id}/growth", response_model=StudentCycleProgress | None)
async def get_student_growth_endpoint(student_id: str):
    progress = await get_student_growth(student_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Student or current cycle not found")
    return progress


@app.get("/api/knowledge/search")
async def knowledge_search_endpoint(q: str = "", limit: int = 5):
    from app.services.knowledge_service import search_knowledge

    if not q:
        return []
    return await search_knowledge(q, limit)


@app.post("/api/homework/generate")
async def homework_generate_endpoint(request: HomeworkGenerateRequest):
    from app.services.homework_service import generate_homework
    result = await generate_homework(
        class_id=request.class_id,
        grade=request.grade,
        student_id=request.student_id,
        error_codes_target=request.error_codes_target or None,
        problem_count=request.problem_count,
        difficulty=request.difficulty,
    )
    return result


@app.get("/api/homework/{homework_id}", response_model=Homework)
async def homework_detail_endpoint(homework_id: str):
    from app.services.homework_service import get_homework

    homework = await get_homework(homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return homework


@app.post("/api/homework/assign")
async def homework_assign_endpoint(homework_id: str, due_date: str | None = None):
    from app.services.homework_service import assign_homework, get_homework
    hw = await get_homework(homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    await assign_homework(homework_id, due_date)
    return {"homework_id": homework_id, "status": "assigned"}


@app.post("/api/homework/submit")
async def homework_submit_endpoint(request: HomeworkSubmitRequest):
    from app.services.grading_service import submit_homework
    result = await submit_homework(request.homework_id, request.student_id, request.answers)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/homework/grade", response_model=HomeworkGradeResult)
async def homework_grade_endpoint(homework_id: str, student_id: str):
    from app.services.grading_service import grade_homework
    result = await grade_homework(homework_id, student_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/homework/{homework_id}/submissions", response_model=list[OCRTaskResponse])
async def homework_submissions_endpoint(homework_id: str):
    from app.services.ocr_service import list_homework_scans

    return await list_homework_scans(homework_id)


@app.post("/api/quiz/generate")
async def quiz_generate_endpoint(request: QuizGenerateRequest):
    from app.services.quiz_service import generate_quiz
    result = await generate_quiz(
        class_id=request.class_id,
        grade=request.grade,
        error_codes_target=request.error_codes_target or None,
        problem_count=request.problem_count,
        difficulty=request.difficulty,
    )
    return result


@app.get("/api/quiz/{quiz_id}", response_model=QuizResponse)
async def quiz_get_endpoint(quiz_id: str):
    from app.services.quiz_service import get_quiz
    quiz = await get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@app.post("/api/quiz/{quiz_id}/response")
async def quiz_response_endpoint(quiz_id: str, record: QuizResponseRecord):
    from app.services.quiz_service import record_response
    quiz = await get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    await record_response(quiz_id, record.problem_sequence, record.class_response, record.notes)
    return {"ok": True}


@app.get("/api/quiz/{quiz_id}/summary", response_model=QuizSummary)
async def quiz_summary_endpoint(quiz_id: str):
    from app.services.quiz_service import get_quiz_summary
    summary = await get_quiz_summary(quiz_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return summary


@app.get("/api/curriculum/units")
async def curriculum_units_endpoint(grade: int = 6, semester: int = 2):
    return await get_units(grade, semester)


@app.get("/api/curriculum/schedule/{class_id}")
async def curriculum_schedule_endpoint(class_id: str):
    return await get_schedule(class_id)


@app.put("/api/curriculum/schedule/{class_id}")
async def curriculum_schedule_update_endpoint(class_id: str, updates: list[dict]):
    count = await update_schedule(class_id, updates)
    return {"updated": count}


@app.get("/api/curriculum/calendar")
async def curriculum_calendar_endpoint(academic_year: str = "2025-2026", semester: int = 2):
    return await get_calendar(academic_year, semester)


@app.get("/api/students/{student_id}/trajectory")
async def student_trajectory_endpoint(student_id: str):
    return await get_student_trajectory(student_id)


@app.patch("/api/students/{student_id}/profile")
async def student_profile_update_endpoint(
    student_id: str,
    personality_tags: list[str] | None = None,
    learning_style: str | None = None,
    notes: str | None = None,
):
    ok = await update_student_profile(student_id, personality_tags, learning_style, notes)
    if not ok:
        raise HTTPException(status_code=400, detail="No fields to update")
    return {"ok": True}


@app.post("/api/homework/{homework_id}/generate-pdf")
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


@app.get("/api/homework/{homework_id}/pdfs")
async def homework_pdf_list_endpoint(homework_id: str):
    from app.services.pdf_service import get_homework_pdf_paths
    return await get_homework_pdf_paths(homework_id)


@app.post("/api/homework/batch-pipeline")
async def homework_batch_pipeline_endpoint(
    class_id: str = "G6A1",
    grade: int = 6,
    semester: int = 1,
    difficulty: str = "A",
    problem_count: int = 5,
    unit_title: str = "",
    use_llm: bool = False,
    teacher_id: str = "T001",
):
    import json
    import uuid
    from datetime import date
    from app.db import get_db
    from app.services.pdf_service import generate_homework_pdf

    if use_llm:
        from app.services.llm_client import generate_math_problems
        try:
            raw_problems = await generate_math_problems(
                grade=grade, semester=semester,
                difficulty=difficulty, count=problem_count,
                unit_title=unit_title,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"DeepSeek API 调用失败: {e}")
    else:
        from app.services.problem_generator import generate_quiz_problems
        generated = generate_quiz_problems(
            error_codes=["E03"], difficulty=difficulty, total_count=problem_count,
        )
        raw_problems = [
            {
                "problem": p.problem,
                "problem_plain": p.problem,
                "correct_answer": p.correct_answer,
                "knowledge_point": p.knowledge_point,
                "target_error_code": p.error_code,
                "difficulty": difficulty,
            }
            for p in generated
        ]

    homework_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()

    async with get_db() as db:
        cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
        class_name = row["name"] if row else class_id

        await db.execute(
            """INSERT INTO homework (id, class_id, grade, knowledge_points,
               error_codes_target, status, generated_by, created_at)
               VALUES (?, ?, ?, ?, ?, 'assigned', ?, ?)""",
            (
                homework_id, class_id, grade,
                json.dumps(list({p.get("knowledge_point", "") for p in raw_problems})),
                json.dumps(list({p.get("target_error_code", "") for p in raw_problems})),
                "deepseek" if use_llm else "system",
                today,
            ),
        )

        for i, p in enumerate(raw_problems, 1):
            pid = f"HP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO homework_problems (id, homework_id, sequence, problem,
                   correct_answer, knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, homework_id, i,
                 p.get("problem_plain", p.get("problem", "")),
                 p.get("correct_answer", ""),
                 p.get("knowledge_point", ""),
                 p.get("target_error_code", ""),
                 p.get("difficulty", difficulty)),
            )
        await db.commit()

    try:
        pdf_path = await generate_homework_pdf(
            homework_id=homework_id,
            class_id=class_id,
            class_name=class_name,
        title=title or unit_title or "课后练习",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")

    return {
        "homework_id": homework_id,
        "class_id": class_id,
        "class_name": class_name,
        "problem_count": len(raw_problems),
        "generated_by": "deepseek" if use_llm else "system",
        "pdf_path": pdf_path,
    }


@app.post("/api/homework/batch-pipeline/class")
async def homework_batch_class_endpoint(
    class_id: str = Body("G6A1"),
    grade: int = Body(6),
    semester: int = Body(1),
    difficulty: str = Body("A"),
    problem_count: int = Body(5),
    unit_title: str = Body(""),
    title: str = Body("课后练习"),
    error_codes: list[str] = Body(["E01", "E02", "E03", "E04", "E05", "E07"]),
    use_llm: bool = Body(False),
):
    from app.services.pdf_service import batch_generate_pdfs
    from app.db import get_db
    import json, uuid
    from datetime import date

    if use_llm:
        from app.services.llm_client import generate_math_problems
        try:
            raw_problems = await generate_math_problems(
                grade=grade, semester=semester,
                difficulty=difficulty, count=problem_count,
                unit_title=unit_title,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"DeepSeek API 调用失败: {e}")
    else:
        from app.services.problem_generator import generate_quiz_problems
        generated = generate_quiz_problems(
            error_codes=error_codes, difficulty=difficulty, total_count=problem_count,
        )
        raw_problems = [
            {
                "problem": p.problem,
                "problem_plain": p.problem,
                "correct_answer": p.correct_answer,
                "knowledge_point": p.knowledge_point,
                "target_error_code": p.error_code,
                "difficulty": difficulty,
            }
            for p in generated
        ]

    homework_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()

    async with get_db() as db:
        cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
        class_name = row["name"] if row else class_id

        await db.execute(
            """INSERT INTO homework (id, class_id, grade, knowledge_points,
               error_codes_target, status, generated_by, created_at)
               VALUES (?, ?, ?, ?, ?, 'assigned', ?, ?)""",
            (
                homework_id, class_id, grade,
                json.dumps(list({p.get("knowledge_point", "") for p in raw_problems})),
                json.dumps(list({p.get("target_error_code", "") for p in raw_problems})),
                "deepseek" if use_llm else "system",
                today,
            ),
        )
        for i, p in enumerate(raw_problems, 1):
            pid = f"HP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO homework_problems (id, homework_id, sequence, problem,
                   correct_answer, knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, homework_id, i,
                 p.get("problem_plain", p.get("problem", "")),
                 p.get("correct_answer", ""),
                 p.get("knowledge_point", ""),
                 p.get("target_error_code", ""),
                 p.get("difficulty", difficulty)),
            )
        await db.commit()

    pdf_paths = await batch_generate_pdfs(
        homework_id=homework_id,
        class_id=class_id,
        class_name=class_name,
        title=unit_title or "课后练习",
    )

    return {
        "homework_id": homework_id,
        "class_id": class_id,
        "class_name": class_name,
        "problem_count": len(raw_problems),
        "pdf_count": len(pdf_paths),
        "pdf_paths": pdf_paths,
        "generated_by": "deepseek" if use_llm else "system",
    }


@app.get("/api/pdfs/{pdf_id}")
async def serve_pdf_endpoint(pdf_id: str):
    """Serve a generated PDF file by its database ID."""
    from pathlib import Path

    from app.db import get_db
    from fastapi.responses import FileResponse

    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM homework_pdfs WHERE id = ?", (pdf_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="PDF 不存在")
        pdf_path = row["pdf_path"]
        if not Path(pdf_path).exists():
            raise HTTPException(status_code=404, detail="PDF 文件缺失")
        student_name = row["student_id"] or "class"
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"homework_{student_name}.pdf",
        )


@app.get("/api/classes/{class_id}/homework-pdfs")
async def class_homework_pdfs_endpoint(class_id: str):
    """List all homework PDFs for a class, newest first."""
    from app.db import get_db

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


@app.get("/api/ocr/stub")
async def ocr_stub_endpoint():
    return {
        "mode": "simulated",
        "message": "OCR is currently simulated for the teacher demo loop.",
        "review_status": "pending_teacher_review",
    }


@app.get("/api/config/llm-status")
async def llm_status_endpoint():
    from app.services.llm_client import get_llm_status
    return get_llm_status()


@app.post("/api/config/llm-mode")
async def llm_mode_endpoint(
    mode: str | None = None,
    proxy_url: str | None = None,
    proxy_model: str | None = None,
    api_key: str | None = None,
):
    from app.services.llm_client import llm_config

    if mode is not None:
        if mode not in ("official", "proxy", "glm"):
            raise HTTPException(status_code=400, detail="mode must be 'official', 'proxy', or 'glm'")
        llm_config.mode = mode
    if proxy_url is not None:
        llm_config.proxy_url = proxy_url.rstrip("/")
    if proxy_model is not None:
        llm_config.proxy_model = proxy_model
    if api_key is not None:
        llm_config.api_key = api_key

    # Invalidate pooled client so next request opens a fresh connection
    await llm_config.close()

    return get_llm_status()


@app.post("/api/ocr/upload", response_model=OCRTaskResponse)
async def ocr_upload_endpoint(request: OCRUploadRequest):
    from app.services.ocr_service import upload_simulated_scan

    result = await upload_simulated_scan(request)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/ocr/submissions/{scan_id}", response_model=OCRTaskResponse)
async def ocr_submission_status_endpoint(scan_id: str):
    from app.services.ocr_service import get_scan_status

    result = await get_scan_status(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan submission not found")
    return result


@app.get("/api/knowledge/points")
async def knowledge_points_endpoint(
    error_code: str | None = None, unit_number: int | None = None,
):
    from app.services.knowledge_rag_service import (
        get_knowledge_points_by_error_code,
        get_knowledge_point_by_id,
    )
    from app.db import get_db

    if error_code:
        return await get_knowledge_points_by_error_code(error_code)

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
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


@app.get("/api/knowledge/graph")
async def knowledge_graph_endpoint(kp_id: str = "KP_E01_01", depth: int = 2):
    from app.services.knowledge_rag_service import (
        get_knowledge_point_by_id,
        get_related_concepts,
    )

    kp = await get_knowledge_point_by_id(kp_id)
    if kp is None:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    related = await get_related_concepts(kp_id, max_depth=depth)
    return {"root": kp, "related": related}


@app.get("/api/curriculum/week-calc")
async def week_calc_endpoint(
    week: int = 1, grade: int = 6, semester: int = 1,
):
    from app.services.knowledge_rag_service import get_week_calc_type

    result = await get_week_calc_type(week, grade, semester)
    if result is None:
        raise HTTPException(status_code=404, detail="No mapping found for this week")
    return result


@app.get("/api/problem-bank")
async def problem_bank_endpoint(
    error_code: str = "E01", difficulty: str = "B", limit: int = 5,
):
    from app.services.knowledge_rag_service import get_example_problems

    return await get_example_problems(error_code, difficulty, limit)


# === Homework Lifecycle ===

@app.post("/api/homework/lifecycle")
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


@app.post("/api/homework/{homework_id}/simulate")
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


@app.post("/api/homework/{homework_id}/ai-grade")
async def ai_grade_homework_endpoint(homework_id: str, class_id: str = "G6A1"):
    from app.services.ai_grading_service import ai_grade_homework

    return await ai_grade_homework(homework_id, class_id)


@app.post("/api/homework/{homework_id}/ai-profile")
async def ai_profile_homework_endpoint(homework_id: str, class_id: str = "G6A1"):
    from app.services.ai_profile_service import ai_update_profiles_after_grading

    return await ai_update_profiles_after_grading(homework_id)


# === AI Student Profile ===

@app.get("/api/students/{student_id}/ai-analysis")
async def ai_student_analysis(student_id: str, homework_id: str | None = None):
    from app.services.ai_profile_service import ai_analyze_student

    return await ai_analyze_student(student_id, homework_id)


@app.get("/api/classes/{class_id}/ai-portrait")
async def ai_class_portrait(class_id: str):
    from app.services.ai_profile_service import ai_analyze_class

    return await ai_analyze_class(class_id)


# === Dify Status ===

@app.get("/api/config/dify-status")
async def dify_status():
    from app.services.dify_client import get_dify_status

    return get_dify_status()
