export type ErrorCode =
  | "OK"
  | "E01"
  | "E02"
  | "E03"
  | "E04"
  | "E05"
  | "E06"
  | "E07"
  | "E08"
  | "E09"
  | "E10"
  | "E11"
  | "E99";

export type GuidanceMode = "standard" | "exploration" | "challenge";

export interface ErrorTag {
  code: ErrorCode;
  label: string;
  confidence: number;
  evidence: string;
  teacher_action: string;
  student_feedback: string;
}

export interface GrowthMilestone {
  current_stage: string;
  days_completed: number;
  total_days_in_cycle: number;
  cycle_type: string;
  tree_species_id: string | null;
}

export interface TreeSpecies {
  id: string;
  name: string;
  category: string;
  emoji: string;
  education_value: string;
  knowledge_highlight: string;
  available_cycles: string[];
}

export interface EncouragementRule {
  trigger: string;
  message: string;
  cumulative_days: number | null;
  start_grade: number | null;
}

export interface PracticeItem {
  problem: string;
  reason: string;
}

export interface StudentGuidance {
  message: string;
  guiding_questions: string[];
  key_takeaway: string;
  next_step: string;
}

export interface DiagnosisResponse {
  record_id: string | null;
  student_id: string;
  is_correct: boolean;
  primary_error: ErrorTag;
  secondary_errors: ErrorTag[];
  normalized: Record<string, unknown>;
  teacher_summary: string;
  guidance_mode: GuidanceMode;
  growth_milestone: GrowthMilestone | null;
  review_status: string;
}

export interface PracticeRecommendationResponse {
  grade: number;
  guidance_mode: GuidanceMode;
  level: string;
  target_error: string;
  items: PracticeItem[];
  estimated_minutes: number;
  review_status: string;
}

export interface DifySessionDraftRequest {
  student_id?: string;
  grade: number;
  problem_text: string;
  correct_answer_text: string | number;
  student_answer_text: string | number;
  student_steps_text?: string | null;
  guidance_mode?: GuidanceMode;
  tree_species_id?: string | null;
  source?: string;
}

export interface DifySessionDraftResponse {
  diagnosis: DiagnosisResponse;
  practice: PracticeRecommendationResponse;
  teacher_summary: string;
  student_feedback: StudentGuidance;
  tree_species: TreeSpecies | null;
  encouragement_message: string | null;
  review_status: string;
}

export const ERROR_LABELS: Record<ErrorCode, string> = {
  OK: "答案正确",
  E01: "基础事实错误",
  E02: "进位错误",
  E03: "退位错误",
  E04: "数位对齐错误",
  E05: "运算顺序错误",
  E06: "小数点/分数单位错误",
  E07: "抄题/转写错误",
  E08: "步骤遗漏",
  E09: "算理理解不足",
  E10: "审题与单位理解错误",
  E11: "习惯性未验算",
  E99: "暂未识别错因",
};

export const GROWTH_STAGES = [
  { key: "seed", label: "播种", day: 1, emoji: "\u{1F331}" },
  { key: "sprout", label: "破土", day: 3, emoji: "\u{1F331}" },
  { key: "first_leaf", label: "第一片叶", day: 7, emoji: "\u{1F33F}" },
  { key: "taller", label: "长高", day: 14, emoji: "\u{1F333}" },
  { key: "branching", label: "分枝", day: 21, emoji: "\u{1F333}" },
  { key: "sturdy", label: "茁壮", day: 30, emoji: "\u{1F333}" },
  { key: "bud", label: "花苞", day: 45, emoji: "\u{1F338}" },
  { key: "flowering", label: "开花", day: 60, emoji: "\u{1F33A}" },
  { key: "mature", label: "成材", day: 90, emoji: "\u{1F332}" },
] as const;

export type GrowthStage = (typeof GROWTH_STAGES)[number]["key"];

export interface WeeklyAccuracy {
  week_number: number;
  accuracy: number;
  total_attempts: number;
  correct_count: number;
}

export interface StudentTree {
  student_id: string;
  student_name: string;
  tree_species_id: string | null;
  tree_species_emoji: string;
  tree_species_name: string;
  current_stage: string;
  days_completed: number;
  total_days: number;
  overall_accuracy: number;
  weekly_accuracy: WeeklyAccuracy[];
  dominant_errors: string[];
  total_attempts: number;
  correct_count: number;
  emotional_state: EmotionState;
  emotional_intensity: number;
  encouragement_needed: boolean;
}

export type EmotionState = "thriving" | "happy" | "stable" | "wilting" | "struggling";

export interface ClassForestResponse {
  class_id: string;
  class_name: string;
  grade: number;
  semester: string;
  academic_year: string;
  cycle_id: string | null;
  week_number: number | null;
  trees: StudentTree[];
  class_accuracy: number;
  class_top_errors: string[];
  class_emotional_state: EmotionState;
}

export interface QuizProblemItem {
  sequence: number;
  problem: string;
  correct_answer: string;
  target_error_code: string | null;
  difficulty: string;
  knowledge_point: string;
  hint: string;
}

export interface QuizResponse {
  quiz_id: string;
  class_id: string;
  title: string;
  status: string;
  target_error_codes: string[];
  difficulty: string;
  problems: QuizProblemItem[];
  created_at: string;
}

export interface QuizSummary {
  quiz_id: string;
  class_id: string;
  total_problems: number;
  responses: Array<{
    id: string;
    quiz_id: string;
    problem_sequence: number;
    class_response: string;
    notes: string;
    created_at: string;
  }>;
  error_distribution: Record<string, number>;
  mostly_correct_count: number;
  mixed_count: number;
  mostly_wrong_count: number;
  recommendation: string;
}

export type WhiteboardStep =
  | "showing_problem"
  | "showing_hint"
  | "revealing_answer"
  | "marking_response"
  | "showing_explanation";

export type ClassResponse = "mostly_correct" | "mixed" | "mostly_wrong";

export interface HealthResponse {
  status: string;
  version: string;
}

export interface ClassSummary {
  class_id: string;
  class_name: string;
  total_students: number;
  total_attempts: number;
  class_accuracy: number;
  top_error_tags: Array<{
    code: string;
    count: number;
  }>;
  students_needing_attention: string[];
  teacher_brief: string;
}

export interface AcademicCycle {
  id: string;
  cycle_type: string;
  academic_year: string;
  grade: number;
  start_date: string;
  end_date: string;
  total_days: number;
  practice_goal_days: number;
  available_tree_species: string[];
}

export type HomeworkStatus =
  | "draft"
  | "assigned"
  | "in_progress"
  | "submitted"
  | "graded"
  | "archived";

export type RecognitionStatus = "queued" | "processing" | "recognized";

export type ArchiveStatus = "pending" | "archived";

export interface HomeworkGenerateRequest {
  class_id: string;
  student_id?: string | null;
  grade: number;
  error_codes_target?: string[];
  problem_count?: number;
  difficulty?: string;
}

export interface HomeworkGenerateResponse {
  homework_id: string;
  problem_count: number;
  error_codes_target: string[];
}

export interface HomeworkProblem {
  id: string;
  homework_id: string;
  sequence: number;
  problem: string;
  correct_answer: string;
  knowledge_point: string;
  target_error_code: string | null;
  difficulty: string;
}

export interface HomeworkDetail {
  id: string;
  class_id: string;
  student_id: string | null;
  cycle_id?: string | null;
  grade: number;
  knowledge_points: string[];
  error_codes_target: string[];
  problems: HomeworkProblem[];
  status: HomeworkStatus;
  assigned_date: string | null;
  due_date: string | null;
  generated_by: string;
  created_at: string;
}

export interface HomeworkGradeResult {
  homework_id: string;
  student_id: string;
  total_problems: number;
  correct_count: number;
  accuracy: number;
  primary_errors: string[];
  profile_updated: boolean;
  growth_updated: boolean;
  next_suggestion: string | null;
}

export interface SimulatedRecognitionAnswer {
  problem_sequence: number;
  raw_answer: string;
  notes?: string | null;
}

export interface RecognizedAnswer {
  problem_sequence: number;
  raw_answer: string;
  recognized_answer: string;
  confidence: number;
  review_status: string;
}

export interface OCRTaskResponse {
  scan_id: string;
  homework_id: string;
  student_id: string;
  recognition_status: RecognitionStatus;
  grading_status: HomeworkStatus;
  archive_status: ArchiveStatus;
  review_status: string;
  uploaded_at: string;
  reviewed_at: string | null;
  recognized_answers: RecognizedAnswer[];
  submission_id: string | null;
  diagnosis: HomeworkGradeResult | null;
}

export interface HomeworkPdfRecord {
  id: string;
  homework_id: string;
  class_id: string;
  student_id: string | null;
  pdf_path: string;
  pdf_type: string;
  generated_at: string;
  grade: number;
  hw_status: string;
  hw_created: string;
}

export interface WeakKnowledgePoint {
  error_code: string;
  unit_id: string;
  unit_title: string;
  knowledge_point: string;
  typical_error: string;
  accuracy: number;
  total_attempts: number;
  mastery_zone: "mastered" | "learning" | "needs_practice";
}

export interface StudentProfile {
  student_id: string;
  student: {
    id: string;
    name: string;
    grade: number;
    class_id: string;
    student_number: string;
    guidance_mode: GuidanceMode;
    textbook_version: string;
    start_grade: number;
    enrolled_at: string;
  };
  total_attempts: number;
  correct_count: number;
  accuracy: number;
  dominant_error_tags: string[];
  accuracy_by_error_code: Record<string, number>;
  weekly_accuracy: WeeklyAccuracy[];
  recent_accuracy_trend: string;
  current_guidance_mode: GuidanceMode;
  growth_milestone: GrowthMilestone | null;
  last_active_date: string | null;
  weak_knowledge_points: WeakKnowledgePoint[];
}
