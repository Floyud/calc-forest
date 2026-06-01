from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field, field_validator


class ErrorCode(str, Enum):
    CORRECT = "OK"
    BASIC_FACT = "E01"
    CARRY = "E02"
    BORROW = "E03"
    PLACE_VALUE_ALIGNMENT = "E04"
    OPERATION_ORDER = "E05"
    DECIMAL_FRACTION_UNIT = "E06"
    TRANSCRIPTION = "E07"
    MISSING_STEP = "E08"
    CONCEPTUAL_UNDERSTANDING = "E09"
    WORDING_UNIT = "E10"
    NO_CHECKING = "E11"
    UNKNOWN = "E99"


class GuidanceMode(str, Enum):
    STANDARD = "standard"
    EXPLORATION = "exploration"
    CHALLENGE = "challenge"


ERROR_LABELS: dict[ErrorCode, str] = {
    ErrorCode.CORRECT: "答案正确",
    ErrorCode.BASIC_FACT: "基础事实错误",
    ErrorCode.CARRY: "进位错误",
    ErrorCode.BORROW: "退位错误",
    ErrorCode.PLACE_VALUE_ALIGNMENT: "数位对齐错误",
    ErrorCode.OPERATION_ORDER: "运算顺序错误",
    ErrorCode.DECIMAL_FRACTION_UNIT: "小数点/分数单位错误",
    ErrorCode.TRANSCRIPTION: "抄题/转写错误",
    ErrorCode.MISSING_STEP: "步骤遗漏",
    ErrorCode.CONCEPTUAL_UNDERSTANDING: "算理理解不足",
    ErrorCode.WORDING_UNIT: "审题与单位理解错误",
    ErrorCode.NO_CHECKING: "习惯性未验算",
    ErrorCode.UNKNOWN: "暂未识别错因",
}


class ErrorTag(BaseModel):
    code: ErrorCode
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    teacher_action: str
    student_feedback: str


class AnswerRecord(BaseModel):
    record_id: str | None = None
    student_id: str | None = Field(default=None)
    grade: int = Field(ge=1, le=6)
    class_id: str | None = None
    knowledge_point: str | None = None
    problem: str
    correct_answer: str
    student_answer: str
    student_steps: list[str] = Field(default_factory=list)
    time_spent_seconds: int | None = Field(default=None, ge=0)
    source: str = "manual"


class DiagnosisRequest(AnswerRecord):
    pass


class GrowthMilestone(BaseModel):
    current_stage: str = "seed"
    days_completed: int = Field(default=0, ge=0)
    total_days_in_cycle: int = Field(default=90, ge=1)
    cycle_type: str = "semester"
    tree_species_id: str | None = None


class TreeSpecies(BaseModel):
    species_id: str
    name: str
    category: str
    emoji: str
    education_value: str
    knowledge_highlight: str
    available_cycles: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def id(self) -> str:
        return self.species_id


class EncouragementRule(BaseModel):
    trigger: str
    message: str
    cumulative_days: int | None = Field(default=None, ge=1)
    start_grade: int | None = Field(default=None, ge=1, le=6)


class PracticeItem(BaseModel):
    problem: str
    reason: str


class PracticeRecommendationRequest(BaseModel):
    error_code: ErrorCode
    grade: int = Field(ge=1, le=6)
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD


class PracticeRecommendationResponse(BaseModel):
    grade: int
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    level: str
    target_error: str
    items: list[PracticeItem] = Field(default_factory=list)
    estimated_minutes: int = Field(default=5, ge=1, le=10)
    review_status: str = "pending_teacher_review"


class StudentGuidance(BaseModel):
    message: str
    guiding_questions: list[str] = Field(default_factory=list)
    key_takeaway: str
    next_step: str


class DifySessionDraftRequest(BaseModel):
    student_id: str = Field(default="S000")
    grade: int = Field(ge=1, le=6)
    problem_text: str
    correct_answer_text: str | int | float
    student_answer_text: str | int | float
    student_steps_text: str | None = None
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    tree_species_id: str | None = None
    source: str = "manual"

    @field_validator("correct_answer_text", "student_answer_text", mode="before")
    @classmethod
    def stringify_numeric_text(cls, value: str | int | float) -> str:
        return str(value)


class DifySessionDraftResponse(BaseModel):
    diagnosis: DiagnosisResponse
    practice: PracticeRecommendationResponse
    teacher_summary: str
    student_feedback: StudentGuidance
    tree_species: TreeSpecies | None = None
    encouragement_message: str | None = None
    review_status: str = "pending_teacher_review"


class Student(BaseModel):
    student_id: str
    name: str
    grade: int = Field(ge=1, le=6)
    class_id: str
    student_number: str = ""
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    textbook_version: str = "PEP"
    start_grade: int = Field(ge=1, le=6)
    enrolled_at: str
    personality_tags: list[str] = Field(default_factory=list)
    learning_style: str = ""
    notes: str = ""


class WeakKnowledgePoint(BaseModel):
    error_code: str
    error_label: str
    unit_id: str
    unit_title: str
    knowledge_point: str
    typical_error: str
    accuracy: float = 0.0
    mastery_zone: Literal["mastered", "learning", "needs_practice"] = "needs_practice"


class StudentProfile(BaseModel):
    student_id: str
    student: Student
    total_attempts: int = 0
    correct_count: int = 0
    accuracy: float = 0.0
    dominant_error_tags: list[str] = Field(default_factory=list)
    accuracy_by_error_code: dict[str, float] = Field(default_factory=dict)
    weak_knowledge_points: list[dict] = Field(default_factory=list)
    weekly_accuracy: list[WeeklyAccuracy] = Field(default_factory=list)
    recent_accuracy_trend: Literal["improving", "declining", "stable"] = "stable"
    current_guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    growth_milestone: GrowthMilestone | None = None
    last_active_date: str | None = None
    archetype: dict[str, Any] | None = None


class WeeklyAccuracy(BaseModel):
    week_number: int
    accuracy: float = 0.0
    total_attempts: int = 0
    correct_count: int = 0


class StudentTree(BaseModel):
    student_id: str
    student_name: str
    tree_species_id: str | None = None
    tree_species_emoji: str = "\U0001F331"
    tree_species_name: str = ""
    current_stage: str = "seed"
    days_completed: int = 0
    total_days: int = 90
    overall_accuracy: float = 0.0
    weekly_accuracy: list[WeeklyAccuracy] = Field(default_factory=list)
    dominant_errors: list[str] = Field(default_factory=list)
    total_attempts: int = 0
    correct_count: int = 0
    emotional_state: str = "stable"
    emotional_intensity: float = 0.0
    encouragement_needed: bool = False


class ClassForestResponse(BaseModel):
    class_id: str
    class_name: str
    grade: int
    semester: str
    academic_year: str
    cycle_id: str | None = None
    week_number: int | None = None
    trees: list[StudentTree] = Field(default_factory=list)
    class_accuracy: float = 0.0
    class_top_errors: list[str] = Field(default_factory=list)
    class_emotional_state: str = "stable"


class Class(BaseModel):
    id: str
    name: str
    grade: int = Field(ge=1, le=6)
    academic_year: str
    semester: str
    student_ids: list[str] = Field(default_factory=list)


class ClassSummary(BaseModel):
    class_id: str
    class_name: str
    total_students: int
    total_attempts: int = 0
    class_accuracy: float = 0.0
    top_error_tags: list[dict[str, int | str]] = Field(default_factory=list)
    students_needing_attention: list[str] = Field(default_factory=list)
    class_weak_points: list[dict] = Field(default_factory=list)
    teacher_brief: str = ""


class AcademicCycle(BaseModel):
    id: str
    cycle_type: str
    academic_year: str
    grade: int = Field(ge=1, le=6)
    start_date: str
    end_date: str
    total_days: int = Field(ge=1)
    practice_goal_days: int = Field(ge=1)
    available_tree_species: list[str] = Field(default_factory=list)


class StudentCycleProgress(BaseModel):
    id: str
    student_id: str
    cycle_id: str
    tree_species_id: str | None = None
    days_completed: int = 0
    current_stage: str = "seed"
    last_practice_date: str | None = None


class DiagnosisRecord(BaseModel):
    id: str
    student_id: str
    class_id: str | None = None
    grade: int
    problem: str
    correct_answer: str
    student_answer: str
    is_correct: bool
    error_code: str
    error_label: str
    confidence: float
    evidence: str = ""
    teacher_action: str = ""
    student_feedback: str = ""
    teacher_summary: str = ""
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    review_status: str = "pending_teacher_review"
    created_at: str = ""


class DiagnosisResponse(BaseModel):
    record_id: str | None
    student_id: str | None
    is_correct: bool
    error_code: str = ""  # convenience: mirrors primary_error.code
    error_label: str = ""  # convenience: mirrors primary_error.label
    confidence: float = 0.0  # convenience: mirrors primary_error.confidence
    primary_error: ErrorTag
    secondary_errors: list[ErrorTag] = Field(default_factory=list)
    normalized: dict[str, Any] = Field(default_factory=dict)
    teacher_summary: str
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD
    growth_milestone: GrowthMilestone | None = None
    review_status: str = "pending_teacher_review"


class HomeworkStatus(str, Enum):
    DRAFT = "draft"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    ARCHIVED = "archived"


class HomeworkProblem(BaseModel):
    id: str
    homework_id: str
    sequence: int
    problem: str
    correct_answer: str
    knowledge_point: str = ""
    target_error_code: str | None = None
    difficulty: str = "A"


class Homework(BaseModel):
    id: str
    homework_id: str | None = None
    class_id: str
    student_id: str | None = None
    cycle_id: str | None = None
    grade: int = Field(ge=1, le=6)
    knowledge_points: list[str] = Field(default_factory=list)
    error_codes_target: list[str] = Field(default_factory=list)
    problems: list[HomeworkProblem] = Field(default_factory=list)
    status: HomeworkStatus = HomeworkStatus.DRAFT
    assigned_date: str | None = None
    due_date: str | None = None
    generated_by: str = "system"
    created_at: str = ""


class HomeworkSubmission(BaseModel):
    id: str
    homework_id: str
    student_id: str
    submitted_at: str
    status: HomeworkStatus = HomeworkStatus.SUBMITTED


class StudentAnswer(BaseModel):
    id: str
    submission_id: str
    homework_id: str
    student_id: str
    problem_sequence: int
    problem: str
    correct_answer: str
    student_answer: str
    is_correct: bool = False
    error_code: str | None = None
    error_label: str | None = None
    confidence: float | None = None
    evidence: str | None = None
    teacher_action: str | None = None
    student_feedback: str | None = None


class HomeworkGenerateRequest(BaseModel):
    class_id: str = "G6C1"
    student_id: str | None = None
    grade: int = Field(default=6, ge=1, le=6)
    error_codes_target: list[str] = Field(default_factory=list)
    problem_count: int = Field(default=5, ge=1, le=10)
    difficulty: Literal["A", "B", "C"] = Field(default="A", description="难度等级")
    exercise_types: list[str] = Field(default_factory=list, description="题型范围: 口算,竖式计算,脱式计算,简便运算,列式计算,图形计算,分数运算,比与比例")
    difficulty_strategy: Literal["auto", "A", "B", "C", "mixed"] = Field(default="auto", description="难度策略: auto=自适应, A/B/C=固定, mixed=均衡")


class HomeworkSubmitRequest(BaseModel):
    homework_id: str
    student_id: str
    answers: list[HomeworkAnswerInput]


class HomeworkAnswerInput(BaseModel):
    problem_sequence: int
    raw_answer: str


class HomeworkGradeResult(BaseModel):
    homework_id: str
    student_id: str
    total_problems: int
    correct_count: int
    accuracy: float
    primary_errors: list[str] = Field(default_factory=list)
    profile_updated: bool = False
    growth_updated: bool = False
    next_suggestion: str | None = None


class HealthResponse(BaseModel):
    ok: bool = True
    service: str = "小学数学计算错因诊断系统"
    version: str = "0.1.0"


class QuizProblemItem(BaseModel):
    sequence: int
    problem: str
    correct_answer: str
    target_error_code: str | None = None
    difficulty: str = "B"
    knowledge_point: str = ""
    hint: str = ""


class QuizGenerateRequest(BaseModel):
    class_id: str = "G6C1"
    grade: int = Field(default=6, ge=1, le=6)
    error_codes_target: list[str] = Field(default_factory=list)
    problem_count: int = Field(default=5, ge=1, le=10)
    difficulty: Literal["A", "B", "C"] = Field(default="B")


class QuizResponse(BaseModel):
    quiz_id: str
    class_id: str
    title: str = ""
    status: str = "draft"
    target_error_codes: list[str] = Field(default_factory=list)
    difficulty: str = "B"
    problems: list[QuizProblemItem] = Field(default_factory=list)
    created_at: str = ""


class QuizResponseRecord(BaseModel):
    quiz_id: str
    problem_sequence: int
    class_response: Literal["mostly_correct", "mixed", "mostly_wrong"] = "mixed"
    notes: str = ""


class QuizSummary(BaseModel):
    quiz_id: str
    class_id: str
    total_problems: int
    responses: list[dict] = Field(default_factory=list)
    error_distribution: dict[str, int] = Field(default_factory=dict)
    mostly_correct_count: int = 0
    mixed_count: int = 0
    mostly_wrong_count: int = 0
    recommendation: str = ""


class Teacher(BaseModel):
    id: str
    name: str
    phone: str | None = None
    avatar: str = ""
    class_ids: list[str] = Field(default_factory=list)
    created_at: str = ""


class TeacherLoginRequest(BaseModel):
    teacher_id: str | None = None
    phone: str | None = None
    password: str = "dev"


class TeacherLoginResponse(BaseModel):
    teacher: Teacher
    token: str
    classes: list[Class] = Field(default_factory=list)


class HomeworkLifecycleRequest(BaseModel):
    class_id: str = "G6C1"
    grade: int = Field(default=6, ge=1, le=6)
    problem_count: int = Field(default=5, ge=1, le=10)
    error_codes: list[str] | None = None
    difficulty: Literal["A", "B", "C"] = Field(default="B")
    unit_title: str = ""
    use_llm: bool = False
    simulate: bool = True
    ai_grade: bool = True
    ai_profile: bool = True


class SimulateRequest(BaseModel):
    class_id: str = "G6C1"


# ---------------------------------------------------------------------------
# Exercise Type Catalog (题型类别库)
# ---------------------------------------------------------------------------

class ExerciseTypeBase(BaseModel):
    """A single exercise subtype (leaf node in the catalog tree)."""
    id: str
    parent_id: str | None = None
    category: str
    name: str
    code: str
    difficulty_range: list[str] = Field(default_factory=lambda: ["A", "B", "C"])
    related_error_codes: list[str] = Field(default_factory=list)
    knowledge_points: list[str] = Field(default_factory=list)
    description: str = ""
    example_problem: str = ""
    example_answer: str = ""
    sort_order: int = 0
    is_active: bool = True
    grade_range: list[int] = Field(default_factory=lambda: [5, 6])
    textbook_unit: str = ""


class ExerciseTypeCategory(BaseModel):
    """A top-level category with its subtypes."""
    id: str
    name: str
    code: str
    description: str = ""
    sort_order: int = 0
    subtypes: list[ExerciseTypeBase] = Field(default_factory=list)


class ExerciseTypeCatalogResponse(BaseModel):
    """Full exercise type catalog as a tree structure."""
    categories: list[ExerciseTypeCategory] = Field(default_factory=list)


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None
