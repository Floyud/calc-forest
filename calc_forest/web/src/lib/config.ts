/**
 * Centralized app configuration.
 * Single source of truth for API base URL, default IDs, etc.
 */

/** FastAPI backend base URL */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

/** Default class ID — matches seeded data in the backend DB */
export const DEFAULT_CLASS_ID = "G6C1";

/** Default student ID for demo / single-student views */
export const DEFAULT_STUDENT_ID = "S001";

/** Default grade (六年级) */
export const DEFAULT_GRADE = 6;
