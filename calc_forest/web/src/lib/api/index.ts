import type {
  AcademicCycle,
  ClassSummary,
  DifySessionDraftRequest,
  DifySessionDraftResponse,
  TreeSpecies,
  EncouragementRule,
  ClassForestResponse,
  HealthResponse,
  QuizResponse,
  QuizSummary,
  StudentProfile,
  HomeworkGenerateRequest,
  HomeworkGenerateResponse,
  HomeworkDetail,
  SimulatedRecognitionAnswer,
  OCRTaskResponse,
  HomeworkGradeResult,
  HomeworkPdfRecord,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getSessionDraft(
  body: DifySessionDraftRequest,
): Promise<DifySessionDraftResponse> {
  return request<DifySessionDraftResponse>("/api/dify/session-draft", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getTreeSpecies(): Promise<TreeSpecies[]> {
  return request<TreeSpecies[]>("/api/tree-species");
}

export function getEncouragements(): Promise<EncouragementRule[]> {
  return request<EncouragementRule[]>("/api/encouragements");
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getClassForest(classId: string): Promise<ClassForestResponse> {
  return request<ClassForestResponse>(`/api/classes/${classId}/forest`);
}

export function getClassSummary(classId: string): Promise<ClassSummary> {
  return request<ClassSummary>(`/api/classes/${classId}/summary`);
}

export function getCurrentCycle(grade: number): Promise<AcademicCycle> {
  return request<AcademicCycle>(`/api/cycles/current?grade=${grade}`);
}

export function getStudentProfile(studentId: string): Promise<StudentProfile> {
  return request<StudentProfile>(`/api/students/${studentId}/profile`);
}

export function generateQuiz(body: {
  class_id: string;
  grade?: number;
  error_codes_target?: string[];
  problem_count?: number;
  difficulty?: string;
}): Promise<{ quiz_id: string; problem_count: number; error_codes_target: string[] }> {
  return request("/api/quiz/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getQuiz(quizId: string): Promise<QuizResponse> {
  return request<QuizResponse>(`/api/quiz/${quizId}`);
}

export function recordQuizResponse(
  quizId: string,
  body: { quiz_id: string; problem_sequence: number; class_response: string; notes: string },
): Promise<{ ok: boolean }> {
  return request(`/api/quiz/${quizId}/response`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getQuizSummary(quizId: string): Promise<QuizSummary> {
  return request<QuizSummary>(`/api/quiz/${quizId}/summary`);
}

export function generateHomework(body: HomeworkGenerateRequest): Promise<HomeworkGenerateResponse> {
  return request("/api/homework/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getHomeworkDetail(homeworkId: string): Promise<HomeworkDetail> {
  return request<HomeworkDetail>(`/api/homework/${homeworkId}`);
}

export function assignHomework(
  homeworkId: string,
  dueDate?: string,
): Promise<{ homework_id: string; status: string }> {
  const params = new URLSearchParams({ homework_id: homeworkId });
  if (dueDate) params.set("due_date", dueDate);
  return request(`/api/homework/assign?${params.toString()}`, {
    method: "POST",
  });
}

export function uploadHomeworkRecognition(body: {
  homework_id: string;
  student_id: string;
  answers: SimulatedRecognitionAnswer[];
  source_label?: string;
}): Promise<OCRTaskResponse> {
  return request("/api/ocr/upload", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getRecognitionTask(scanId: string): Promise<OCRTaskResponse> {
  return request<OCRTaskResponse>(`/api/ocr/submissions/${scanId}`);
}

export function getHomeworkSubmissions(homeworkId: string): Promise<OCRTaskResponse[]> {
  return request<OCRTaskResponse[]>(`/api/homework/${homeworkId}/submissions`);
}

export function gradeHomework(
  homeworkId: string,
  studentId: string,
): Promise<HomeworkGradeResult> {
  const params = new URLSearchParams({ homework_id: homeworkId, student_id: studentId });
  return request<HomeworkGradeResult>(`/api/homework/grade?${params.toString()}`, {
    method: "POST",
  });
}

export function getClassHomeworkPdfs(classId: string): Promise<HomeworkPdfRecord[]> {
  return request<HomeworkPdfRecord[]>(`/api/classes/${classId}/homework-pdfs`);
}

export function getPdfUrl(pdfId: string): string {
  return `${API_BASE}/api/pdfs/${pdfId}`;
}

export async function getGuidanceContext(studentId: string): Promise<string> {
  try {
    const res = await fetch(`${API_BASE}/api/guidance/context/${studentId}`);
    if (!res.ok) return "";
    const data = await res.json();
    return data.context || "";
  } catch {
    return "";
  }
}

export async function patchStudentProfile(
  studentId: string,
  data: {
    personality_tags?: string[];
    learning_style?: string;
    notes?: string;
  },
): Promise<{ ok: boolean }> {
  const params = new URLSearchParams();
  if (data.personality_tags !== undefined) {
    for (const tag of data.personality_tags) {
      params.append("personality_tags", tag);
    }
  }
  if (data.learning_style !== undefined) {
    params.set("learning_style", data.learning_style);
  }
  if (data.notes !== undefined) {
    params.set("notes", data.notes);
  }
  return request<{ ok: boolean }>(
    `/api/students/${studentId}/profile?${params.toString()}`,
    { method: "PATCH" },
  );
}
