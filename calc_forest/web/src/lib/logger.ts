"use client";

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  event: string;
  timestamp: string;
  url?: string;
  userAgent?: string;
  [key: string]: unknown;
}

const LOG_ENDPOINT = "/api/logs";
const FLUSH_INTERVAL_MS = 5_000;
const MAX_BATCH_SIZE = 20;
const MAX_QUEUE_SIZE = 100;

let _queue: LogEntry[] = [];
let _flushTimer: ReturnType<typeof setInterval> | null = null;
let _initialized = false;

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const _minLevel: LogLevel =
  (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel) ??
  (process.env.NODE_ENV === "production" ? "warn" : "debug");

function shouldLog(level: LogLevel): boolean {
  return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[_minLevel];
}

function enqueue(entry: LogEntry): void {
  if (_queue.length >= MAX_QUEUE_SIZE) {
    _queue.shift();
  }
  _queue.push(entry);

  if (_queue.length >= MAX_BATCH_SIZE) {
    void flush();
  }
}

async function flush(): Promise<void> {
  if (_queue.length === 0) return;

  const batch = _queue.splice(0);

  try {
    await fetch(`${API_BASE}${LOG_ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logs: batch }),
      keepalive: true,
    });
  } catch {
    const errors = batch.filter((e) => e.level === "error");
    if (errors.length > 0 && _queue.length < MAX_QUEUE_SIZE) {
      _queue.push(...errors.slice(0, MAX_QUEUE_SIZE - _queue.length));
    }
  }
}

function startFlushTimer(): void {
  if (_flushTimer) return;
  _flushTimer = setInterval(() => void flush(), FLUSH_INTERVAL_MS);

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") void flush();
  });
}

function consoleFormat(
  level: LogLevel,
  event: string,
  data: Record<string, unknown>,
): void {
  const ts = new Date().toISOString().slice(11, 19);
  const prefix = `[${ts}] [${level.toUpperCase()}]`;
  const msg = `${prefix} ${event}`;

  switch (level) {
    case "debug":
      console.debug(msg, data);
      break;
    case "info":
      console.info(msg, data);
      break;
    case "warn":
      console.warn(msg, data);
      break;
    case "error":
      console.error(msg, data);
      break;
  }
}

function createEntry(
  level: LogLevel,
  event: string,
  data?: Record<string, unknown>,
): LogEntry {
  return {
    level,
    event,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    userAgent: navigator.userAgent,
    ...data,
  };
}

export const logger = {
  debug(event: string, data?: Record<string, unknown>): void {
    if (!shouldLog("debug")) return;
    const entry = createEntry("debug", event, data);
    consoleFormat("debug", event, data ?? {});
    enqueue(entry);
  },

  info(event: string, data?: Record<string, unknown>): void {
    if (!shouldLog("info")) return;
    const entry = createEntry("info", event, data);
    consoleFormat("info", event, data ?? {});
    enqueue(entry);
  },

  warn(event: string, data?: Record<string, unknown>): void {
    if (!shouldLog("warn")) return;
    const entry = createEntry("warn", event, data);
    consoleFormat("warn", event, data ?? {});
    enqueue(entry);
  },

  error(event: string, data?: Record<string, unknown>): void {
    if (!shouldLog("error")) return;
    const entry = createEntry("error", event, data);
    consoleFormat("error", event, data ?? {});
    enqueue(entry);
  },

  init(): void {
    if (_initialized) return;
    _initialized = true;

    startFlushTimer();

    window.onerror = (message, source, lineno, colno, error) => {
      logger.error("window.onerror", {
        message: String(message),
        source: source ?? undefined,
        lineno,
        colno,
        stack: error?.stack ?? undefined,
      });
    };

    window.addEventListener("unhandledrejection", (event) => {
      const reason = event.reason;
      logger.error("unhandledrejection", {
        reason: String(reason),
        stack: reason?.stack ?? undefined,
      });
    });
  },

  flush,
};
