"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Loader2,
  Pencil,
  Plus,
  Save,
  Send,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  SectionPanel,
  WorkspacePage,
} from "@/components/layout/workspace-shell";
import { API_BASE, DEFAULT_CLASS_ID } from "@/lib/config";
const DAYS = ["周一", "周二", "周三", "周四", "周五"];
const PERIODS = [1, 2, 3, 4, 5, 6];

/** Period time labels — matches the API contract default */
const PERIOD_TIMES: Record<number, string> = {
  1: "8:30–9:10",
  2: "9:20–10:00",
  3: "10:30–11:10",
  4: "11:20–11:50",
  5: "14:30–15:10",
  6: "15:20–16:00",
};

/** Break row inserted after this period */
const BREAK_AFTER_PERIOD = 2;
const BREAK_LABEL = "花样跳绳";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface TimetableEntry {
  day_of_week: number;
  period_number: number;
  subject: string;
  teacher: string;
  is_active: boolean;
  time_label: string;
}

interface WeekView {
  timetable: TimetableEntry[];
  period_times: Record<string, string>;
  break_after_period: number;
  break_label: string;
  total_periods: number;
  assignments: Array<{
    homework_id: string;
    assigned_date: string;
    day_of_week: number;
    problem_count: number;
  }>;
}

interface EditSlot {
  day_of_week: number;
  period_number: number;
  subject: string;
  is_active: boolean;
}

/* ------------------------------------------------------------------ */
/*  Subject styling map                                                */
/* ------------------------------------------------------------------ */

const SUBJECT_STYLES: Record<string, { bg: string; text: string; ring?: string }> = {
  数学: {
    bg: "bg-emerald-500",
    text: "text-white",
    ring: "ring-2 ring-emerald-300 shadow-md",
  },
  语文: { bg: "bg-blue-50", text: "text-blue-700" },
  英语: { bg: "bg-violet-50", text: "text-violet-700" },
  体育: { bg: "bg-orange-50", text: "text-orange-700" },
  音乐: { bg: "bg-pink-50", text: "text-pink-700" },
  美术: { bg: "bg-amber-50", text: "text-amber-700" },
  科学: { bg: "bg-cyan-50", text: "text-cyan-700" },
  道法: { bg: "bg-rose-50", text: "text-rose-700" },
  信息科技: { bg: "bg-indigo-50", text: "text-indigo-700" },
  劳动: { bg: "bg-lime-50", text: "text-lime-700" },
  班会: { bg: "bg-sky-50", text: "text-sky-700" },
};

const FALLBACK_STYLE = { bg: "bg-gray-50", text: "text-gray-600" };

function getSubjectStyle(subject: string) {
  return SUBJECT_STYLES[subject] ?? FALLBACK_STYLE;
}

function isMath(subject: string) {
  return subject === "数学";
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function SchedulePage() {
  const [weekView, setWeekView] = useState<WeekView | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editSlots, setEditSlots] = useState<EditSlot[]>([]);
  const [saving, setSaving] = useState(false);
  const [assigning, setAssigning] = useState<number | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }, []);

  /* ---- Data fetching ---- */
  const fetchWeek = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/timetable/${DEFAULT_CLASS_ID}/full-week-view`
      );
      if (res.ok) {
        const data: WeekView = await res.json();
        setWeekView(data);
        setEditSlots(
          (data.timetable || []).map((e) => ({
            day_of_week: e.day_of_week,
            period_number: e.period_number,
            subject: e.subject,
            is_active: e.is_active,
          }))
        );
        setLoading(false);
        return;
      }
    } catch {
      /* fall through to defaults */
    }
    /* Fallback: build a reasonable demo schedule */
    const defaultTimetable = buildDemoTimetable();
    setWeekView({
      timetable: defaultTimetable,
      period_times: PERIOD_TIMES,
      break_after_period: BREAK_AFTER_PERIOD,
      break_label: BREAK_LABEL,
      total_periods: 6,
      assignments: [],
    });
    setEditSlots(
      defaultTimetable.map((e) => ({
        day_of_week: e.day_of_week,
        period_number: e.period_number,
        subject: e.subject,
        is_active: e.is_active,
      }))
    );
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchWeek();
  }, [fetchWeek]);

  /* ---- Lookup helpers ---- */
  const todayDow = useMemo(() => ((new Date().getDay() + 6) % 7) + 1, []);

  const timetable = weekView?.timetable ?? [];

  /** Build a (day, period) → entry map for O(1) lookup */
  const entryMap = useMemo(() => {
    const m = new Map<string, TimetableEntry>();
    for (const e of timetable) {
      m.set(`${e.day_of_week}-${e.period_number}`, e);
    }
    return m;
  }, [timetable]);

  const periodTimes: Record<string, string> = weekView?.period_times ?? Object.fromEntries(Object.entries(PERIOD_TIMES));
  const breakAfter = weekView?.break_after_period ?? BREAK_AFTER_PERIOD;
  const breakLabel = weekView?.break_label ?? BREAK_LABEL;

  const getEntry = (day: number, period: number) =>
    entryMap.get(`${day}-${period}`);

  const getAssignmentForDay = (day: number) =>
    weekView?.assignments?.find((a) => a.day_of_week === day);

  /* ---- Edit mode ---- */
  const toggleSlot = (day: number, period: number) => {
    setEditSlots((prev) =>
      prev.map((s) =>
        s.day_of_week === day && s.period_number === period
          ? { ...s, is_active: !s.is_active, subject: s.is_active ? s.subject : "数学" }
          : s
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const activeEntries = editSlots
        .filter((s) => s.is_active)
        .map((s) => ({
          day_of_week: s.day_of_week,
          period_number: s.period_number,
          subject: s.subject,
          is_active: s.is_active,
        }));
      const res = await fetch(`${API_BASE}/api/timetable/${DEFAULT_CLASS_ID}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: activeEntries }),
      });
      if (res.ok) {
        showToast("课表已保存");
        setEditing(false);
        fetchWeek();
      }
    } catch {
      showToast("保存失败");
    }
    setSaving(false);
  };

  /* ---- Auto-assign homework ---- */
  const handleAutoAssign = async (dayOfWeek: number) => {
    setAssigning(dayOfWeek);
    try {
      const res = await fetch(
        `${API_BASE}/api/timetable/${DEFAULT_CLASS_ID}/auto-assign`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );
      if (res.ok) {
        const result = await res.json();
        if (result.status === "assigned") {
          showToast(`已自动布置: ${result.homework_id}`);
        } else {
          showToast(result.message || "无法布置");
        }
        fetchWeek();
      } else {
        const err = await res.json();
        showToast(err.detail || "布置失败");
      }
    } catch {
      showToast("布置失败");
    }
    setAssigning(null);
  };

  /* ---- Stats ---- */
  const todayMathCount = useMemo(
    () =>
      timetable.filter(
        (e) => e.day_of_week === todayDow && isMath(e.subject) && e.is_active
      ).length,
    [timetable, todayDow]
  );

  const weekMathCount = useMemo(
    () => timetable.filter((e) => isMath(e.subject) && e.is_active).length,
    [timetable]
  );

  /* ---- Which periods to render (with break row) ---- */
  const rows: Array<{ type: "period"; period: number } | { type: "break" }> =
    useMemo(() => {
      const r: Array<{ type: "period"; period: number } | { type: "break" }> =
        [];
      for (const p of PERIODS) {
        r.push({ type: "period", period: p });
        if (p === breakAfter) {
          r.push({ type: "break" });
        }
      }
      return r;
    }, [breakAfter]);

  /* ================================================================ */
  /*  RENDER                                                          */
  /* ================================================================ */

  return (
    <WorkspacePage>
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--tone-ink)] flex items-center gap-2">
            <CalendarClock className="w-6 h-6" />
            每周课表
          </h1>
          <p className="text-sm text-[var(--tone-muted)] mt-1">
            班级全科目周课表 · 数学课时段自动布置作业
          </p>
        </div>
        <button
          onClick={editing ? handleSave : () => setEditing(true)}
          disabled={saving}
          className={cn(
            "flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-medium transition-all",
            editing
              ? "bg-emerald-600 text-white hover:bg-emerald-700"
              : "bg-white text-[var(--tone-ink)] ring-1 ring-[color:var(--tone-line)] hover:bg-emerald-50"
          )}
        >
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : editing ? (
            <Save className="w-4 h-4" />
          ) : (
            <Pencil className="w-4 h-4" />
          )}
          {editing ? (saving ? "保存中..." : "保存课表") : "编辑课表"}
        </button>
      </div>

      {/* ── Edit hint ── */}
      {editing && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-800 flex items-start gap-2">
          <Clock className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            编辑模式下，点击数学课格子可标记/取消数学课时段。只有标记的数学课时段会用于自动布置作业。
          </span>
          <button onClick={() => setEditing(false)} className="ml-auto shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Timetable grid ── */}
      <SectionPanel
        title="班级课表"
        description="全科目周课表一览，数学课高亮显示"
      >
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
          </div>
        ) : (
          <div className="overflow-x-auto -mx-1 px-1">
            <table className="w-full border-collapse min-w-[640px]">
              {/* ── Header row ── */}
              <thead>
                <tr>
                  <th className="p-3 text-xs text-[var(--tone-muted)] text-left w-[72px] font-normal">
                    时间
                  </th>
                  <th className="p-3 text-xs text-[var(--tone-muted)] text-center w-12 font-normal">
                    节次
                  </th>
                  {DAYS.map((d, i) => (
                    <th
                      key={d}
                      className={cn(
                        "p-3 text-sm font-semibold text-center transition-colors",
                        i + 1 === todayDow
                          ? "text-emerald-700 bg-emerald-50/70 rounded-t-2xl"
                          : "text-[var(--tone-ink)]"
                      )}
                    >
                      {d}
                      {i + 1 === todayDow && (
                        <span className="block text-[10px] text-emerald-500 font-medium mt-0.5">
                          今天
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {rows.map((row, rowIdx) => {
                  /* ──── Break row ──── */
                  if (row.type === "break") {
                    return (
                      <tr key="break">
                        <td
                          colSpan={7}
                          className="py-3"
                        >
                          <div className="flex items-center gap-3 px-2">
                            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--tone-line)] to-transparent" />
                            <span className="text-xs font-medium text-[var(--tone-muted)] whitespace-nowrap flex items-center gap-1.5">
                              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" />
                              {breakLabel}
                            </span>
                            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--tone-line)] to-transparent" />
                          </div>
                        </td>
                      </tr>
                    );
                  }

                  /* ──── Period row ──── */
                  const period = row.period;
                  const timeLabel = periodTimes[String(period)] ?? "";

                  return (
                    <tr key={period}>
                      {/* Time label */}
                      <td className="py-2 pr-1 text-[11px] text-[var(--tone-muted)] text-right align-middle whitespace-nowrap font-mono tabular-nums">
                        {timeLabel}
                      </td>

                      {/* Period number */}
                      <td className="py-2 px-1 text-xs text-[var(--tone-muted)] text-center align-middle">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[var(--tone-soft)] text-[var(--tone-muted)] text-[11px] font-medium">
                          {period}
                        </span>
                      </td>

                      {/* Day cells */}
                      {DAYS.map((_, di) => {
                        const day = di + 1;
                        const entry = getEntry(day, period);
                        const isToday = day === todayDow;
                        const assignment = isToday
                          ? getAssignmentForDay(day)
                          : null;

                        /* In edit mode — show toggleable math buttons */
                        if (editing) {
                          const editSlot = editSlots.find(
                            (s) =>
                              s.day_of_week === day &&
                              s.period_number === period
                          );
                          const isActive = editSlot?.is_active ?? false;

                          return (
                            <td
                              key={day}
                              className={cn(
                                "p-1.5 text-center align-middle",
                                isToday && "bg-emerald-50/30"
                              )}
                            >
                              <button
                                onClick={() => toggleSlot(day, period)}
                                className={cn(
                                  "w-full h-14 rounded-xl text-sm font-medium transition-all duration-200",
                                  isActive
                                    ? "bg-emerald-500 text-white shadow-sm ring-2 ring-emerald-300"
                                    : "bg-gray-50 text-gray-400 hover:bg-gray-100"
                                )}
                              >
                                {isActive ? "数学" : "—"}
                              </button>
                            </td>
                          );
                        }

                        /* Normal mode — show subject cells */
                        if (!entry || !entry.is_active) {
                          return (
                            <td
                              key={day}
                              className={cn(
                                "p-1.5 align-middle",
                                isToday && "bg-emerald-50/20"
                              )}
                            />
                          );
                        }

                        const subject = entry.subject;
                        const teacher = entry.teacher;
                        const math = isMath(subject);
                        const style = getSubjectStyle(subject);

                        return (
                          <td
                            key={day}
                            className={cn(
                              "p-1.5 align-middle",
                              isToday && !math && "bg-emerald-50/20"
                            )}
                          >
                            <div
                              className={cn(
                                "relative flex flex-col items-center justify-center gap-0.5 rounded-xl px-2 py-2.5 transition-all duration-200",
                                /* Math: dominant, striking */
                                math &&
                                  "bg-emerald-500 text-white font-bold text-base shadow-lg ring-2 ring-emerald-300 min-h-[64px]",
                                /* Other subjects: subtle, gentle */
                                !math && style.bg,
                                !math && style.text,
                                !math && "text-sm font-medium min-h-[56px]",
                                /* Today's column gets extra glow for math */
                                math && isToday && "ring-emerald-400 shadow-emerald-200/50"
                              )}
                            >
                              {/* Subject name */}
                              <span className="leading-tight">{subject}</span>

                              {/* Teacher name */}
                              <span
                                className={cn(
                                  "text-[11px] leading-tight",
                                  math
                                    ? "text-emerald-100"
                                    : "opacity-60"
                                )}
                              >
                                {teacher}
                              </span>

                              {/* Auto-assign button — only for today's math */}
                              {math && isToday && (
                                <button
                                  onClick={() => handleAutoAssign(day)}
                                  disabled={assigning === day}
                                  className={cn(
                                    "flex items-center gap-1 mt-1 text-[10px] px-2 py-0.5 rounded-full transition-all",
                                    assignment
                                      ? "bg-emerald-400/30 text-emerald-100"
                                      : "bg-white/20 text-white hover:bg-white/30"
                                  )}
                                >
                                  {assigning === day ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : assignment ? (
                                    <CheckCircle2 className="w-3 h-3" />
                                  ) : (
                                    <Send className="w-3 h-3" />
                                  )}
                                  {assignment ? "已布置" : "布置作业"}
                                </button>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionPanel>

      {/* ── Today status ── */}
      <SectionPanel title="今日状态" description="当天数学课与作业布置情况">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-[var(--tone-line)] bg-white/80 p-5">
            <p className="text-xs text-[var(--tone-muted)] uppercase tracking-wide">
              今日数学课
            </p>
            <p className="text-2xl font-bold text-[var(--tone-ink)] mt-2">
              {todayMathCount}
              <span className="text-sm font-normal text-[var(--tone-muted)] ml-1">
                节
              </span>
            </p>
            <p className="text-[11px] text-[var(--tone-muted)] mt-1">
              本周共 {weekMathCount} 节数学课
            </p>
          </div>
          <div className="rounded-2xl border border-[var(--tone-line)] bg-white/80 p-5">
            <p className="text-xs text-[var(--tone-muted)] uppercase tracking-wide">
              已布置作业
            </p>
            <p className="text-2xl font-bold text-[var(--tone-ink)] mt-2">
              {weekView?.assignments?.length ?? 0}
              <span className="text-sm font-normal text-[var(--tone-muted)] ml-1">
                份
              </span>
            </p>
          </div>
          <div className="rounded-2xl border border-[var(--tone-line)] bg-white/80 p-5 flex items-center justify-center">
            <button
              onClick={() => handleAutoAssign(todayDow)}
              disabled={assigning !== null}
              className="flex items-center gap-2 bg-emerald-600 text-white rounded-xl px-5 py-3 text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              {assigning !== null ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              一键布置今日作业
            </button>
          </div>
        </div>
      </SectionPanel>

      {/* ── Toast ── */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-[var(--tone-ink)] text-white rounded-2xl px-5 py-3 text-sm shadow-lg animate-in fade-in slide-in-from-bottom-4 z-50">
          {toast}
        </div>
      )}
    </WorkspacePage>
  );
}

/* ------------------------------------------------------------------ */
/*  Demo data builder (fallback when API is unreachable)               */
/* ------------------------------------------------------------------ */

function buildDemoTimetable(): TimetableEntry[] {
  const schedule: Record<number, Record<number, { subject: string; teacher: string }>> = {
    1: {
      1: { subject: "语文", teacher: "小田老师" },
      2: { subject: "数学", teacher: "林老师" },
      3: { subject: "英语", teacher: "王老师" },
      4: { subject: "体育", teacher: "赵老师" },
      5: { subject: "美术", teacher: "陈老师" },
      6: { subject: "班会", teacher: "小田老师" },
    },
    2: {
      1: { subject: "数学", teacher: "林老师" },
      2: { subject: "语文", teacher: "小田老师" },
      3: { subject: "科学", teacher: "周老师" },
      4: { subject: "音乐", teacher: "李老师" },
      5: { subject: "语文", teacher: "小田老师" },
      6: { subject: "综合实践", teacher: "赵老师" },
    },
    3: {
      1: { subject: "语文", teacher: "小田老师" },
      2: { subject: "数学", teacher: "林老师" },
      3: { subject: "道德与法治", teacher: "张老师" },
      4: { subject: "信息技术", teacher: "吴老师" },
      5: { subject: "英语", teacher: "王老师" },
      6: { subject: "体育", teacher: "赵老师" },
    },
    4: {
      1: { subject: "数学", teacher: "林老师" },
      2: { subject: "英语", teacher: "王老师" },
      3: { subject: "语文", teacher: "小田老师" },
      4: { subject: "科学", teacher: "周老师" },
      5: { subject: "数学", teacher: "林老师" },
      6: { subject: "美术", teacher: "陈老师" },
    },
    5: {
      1: { subject: "语文", teacher: "小田老师" },
      2: { subject: "数学", teacher: "林老师" },
      3: { subject: "阅读", teacher: "小田老师" },
      4: { subject: "音乐", teacher: "李老师" },
      5: { subject: "写字", teacher: "小田老师" },
      6: { subject: "体育", teacher: "赵老师" },
    },
  };

  const entries: TimetableEntry[] = [];
  for (let day = 1; day <= 5; day++) {
    for (let period = 1; period <= 6; period++) {
      const cell = schedule[day]?.[period];
      entries.push({
        day_of_week: day,
        period_number: period,
        subject: cell?.subject ?? "数学",
        teacher: cell?.teacher ?? "林老师",
        is_active: true,
        time_label: PERIOD_TIMES[period] ?? "",
      });
    }
  }
  return entries;
}
