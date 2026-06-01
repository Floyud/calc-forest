import type {
  AcademicCycle,
  AIGradingResult,
  ClassHomeworkAnalytics,
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
  StudentMasteryResponse,
  HomeworkGenerateRequest,
  HomeworkGenerateResponse,
  HomeworkDetail,
  SimulatedRecognitionAnswer,
  OCRTaskResponse,
  HomeworkGradeResult,
  HomeworkPdfRecord,
  ScanGradeResponse,
  SubmitHomeworkRequest,
  SubmitHomeworkResponse,
} from "@/lib/types";
import { logger } from "@/lib/logger";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 45_000;
const MAX_RETRIES = 2;
const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string,
  ) {
    super(`API ${status}: ${statusText}`);
    this.name = "ApiError";
  }

  get isRetryable(): boolean {
    return RETRYABLE_STATUS_CODES.has(this.status);
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get displayMessage(): string {
    if (this.status === 0) return "网络连接失败，请检查后端服务是否启动";
    if (this.status === 401) return "登录已过期，请重新登录";
    if (this.status === 403) return "没有权限执行此操作";
    if (this.status === 404) return "请求的资源不存在";
    if (this.status >= 500) return "服务器暂时无法响应，请稍后重试";
    return `请求失败 (${this.status})`;
  }
}

async function request<T>(path: string, init?: RequestInit, retries = MAX_RETRIES): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const method = init?.method ?? "GET";

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...init,
    });

    if (!res.ok) {
      const text = await res.text();
      const error = new ApiError(res.status, res.statusText, text);

      if (error.isRetryable && retries > 0) {
        logger.warn("api_retry", { method, path, status: res.status, retriesLeft: retries - 1 });
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return request<T>(path, init, retries - 1);
      }

      logger.error("api_error", { method, path, status: res.status, statusText: res.statusText });
      throw error;
    }

    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof ApiError) throw err;

    if (err instanceof DOMException && err.name === "AbortError") {
      logger.error("api_timeout", { method, path });
      throw new ApiError(0, "Timeout", "请求超时");
    }

    if (err instanceof TypeError && err.message.includes("fetch")) {
      logger.error("api_network_error", { method, path });
      throw new ApiError(0, "Network Error", "无法连接到服务器");
    }

    logger.error("api_unknown_error", { method, path, error: String(err) });
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
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

export function submitHomework(body: SubmitHomeworkRequest): Promise<SubmitHomeworkResponse> {
  const answers = Object.entries(body.answers).map(([sequence, rawAnswer]) => ({
    problem_sequence: Number(sequence),
    raw_answer: rawAnswer,
  }));
  return request<SubmitHomeworkResponse>("/api/homework/submit", {
    method: "POST",
    body: JSON.stringify({ ...body, answers }),
  });
}

export function aiGradeHomework(
  homeworkId: string,
  classId: string,
): Promise<AIGradingResult> {
  return request<AIGradingResult>(`/api/homework/${homeworkId}/ai-grade`, {
    method: "POST",
    body: JSON.stringify({ class_id: classId }),
  });
}

export function getClassHomeworkPdfs(classId: string): Promise<HomeworkPdfRecord[]> {
  return request<HomeworkPdfRecord[]>(`/api/classes/${classId}/homework-pdfs`);
}

export function getPdfUrl(pdfId: string): string {
  if (!API_BASE) return `/api/pdfs/${pdfId}`;
  return `${API_BASE}/api/pdfs/${pdfId}`;
}

async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...init,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new ApiError(res.status, res.statusText, text);
    }

    return res.blob();
  } catch (err) {
    if (err instanceof ApiError) throw err;

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "Timeout", "请求超时");
    }

    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function generateTTSAudio(text: string): Promise<Blob> {
  return requestBlob("/api/tts/generate", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function sendDifyChat(params: {
  inputs: Record<string, string>;
  query: string;
  user: string;
  conversation_id: string;
  history?: Array<{ role: "user" | "bot"; content: string }>;
}): Promise<{ answer: string; conversation_id: string }> {
  return request("/api/dify/chat", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function getStudentMastery(studentId: string): Promise<StudentMasteryResponse> {
  return request<StudentMasteryResponse>(`/api/students/${studentId}/mastery`);
}

export async function loginTeacher(teacherId?: string): Promise<{
  teacher: { id: string; name: string; phone: string };
  classes: Array<{ id: string }>;
  token: string;
}> {
  const body = teacherId ? { teacher_id: teacherId } : {};
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
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
    guidance_mode?: string;
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
  if (data.guidance_mode !== undefined) {
    params.set("guidance_mode", data.guidance_mode);
  }
  return request<{ ok: boolean }>(
    `/api/students/${studentId}/profile?${params.toString()}`,
    { method: "PATCH" },
  );
}

export async function getClassHomeworkAnalytics(
  classId: string,
  limit?: number,
): Promise<ClassHomeworkAnalytics> {
  const params = new URLSearchParams();
  if (limit) params.set("limit", String(limit));
  const qs = params.toString();
  return request<ClassHomeworkAnalytics>(
    `/api/homework/class/${classId}/analytics${qs ? `?${qs}` : ""}`,
  );
}

export async function getHomeworkAnalytics(
  homeworkId: string,
): Promise<ClassHomeworkAnalytics> {
  return request<ClassHomeworkAnalytics>(
    `/api/homework/${homeworkId}/analytics`,
  );
}

export async function scanAndGradeHomework(
  homeworkId: string,
  studentId: string,
  file: File,
  retries = MAX_RETRIES,
): Promise<ScanGradeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("student_id", studentId);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/api/homework/${homeworkId}/scan-grade`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text();
      const error = new ApiError(res.status, res.statusText, text);

      if (error.isRetryable && retries > 0) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return scanAndGradeHomework(homeworkId, studentId, file, retries - 1);
      }

      throw error;
    }

    return res.json() as Promise<ScanGradeResponse>;
  } catch (err) {
    if (err instanceof ApiError) throw err;

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "Timeout", "请求超时");
    }

    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new ApiError(0, "Network Error", "无法连接到服务器");
    }

    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
