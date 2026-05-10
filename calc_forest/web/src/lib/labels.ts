/**
 * Shared Chinese label maps for all user-visible enum values.
 *
 * IMPORTANT: These are display-only. API requests still send English values.
 */

// ─── Homework / OCR / Archive statuses ───

export const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  in_progress: "进行中",
  assigned: "已布置",
  submitted: "已提交",
  queued: "排队中",
  processing: "识别中",
  recognized: "已识别",
  graded: "已批改",
  archived: "已归档",
  completed: "已完成",
};

export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

// ─── Review statuses ───

export const REVIEW_LABELS: Record<string, string> = {
  pending_teacher_review: "待教师审核",
  reviewed: "已审核",
  pending: "待审核",
};

export function getReviewLabel(status: string): string {
  return REVIEW_LABELS[status] ?? status;
}

// ─── Growth stage labels ───

export const STAGE_LABELS: Record<string, string> = {
  seed: "播种",
  sprout: "破土",
  first_leaf: "第一片叶",
  taller: "长高",
  branching: "分枝",
  sturdy: "茁壮",
  bud: "花苞",
  flowering: "开花",
  mature: "成材",
};

export function getStageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? "播种";
}

// ─── Error code "general" fallback ───

export const ERROR_CODE_DISPLAY: Record<string, string> = {
  general: "综合",
};

export function getErrorCodeDisplay(code: string | null | undefined): string {
  if (!code) return "综合";
  return ERROR_CODE_DISPLAY[code] ?? code;
}
