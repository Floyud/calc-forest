"use client";

import { useMemo, useState, useCallback, memo } from "react";
import { useQueries } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, Grid3X3 } from "lucide-react";
import { getStudentProfile } from "@/lib/api";
import type { StudentTree, ErrorCode, StudentProfile } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";

// ─── Error codes displayed in heatmap columns ───

const ERROR_CODES: ErrorCode[] = [
  "E01", "E02", "E03", "E04", "E05",
  "E06", "E07", "E08", "E09", "E10", "E11",
];

// ─── Color thresholds ───

function cellColor(accuracy: number | null): string {
  if (accuracy === null) return "bg-muted/40 text-muted-foreground/50";
  if (accuracy >= 0.85) return "bg-emerald-100/80 text-emerald-700";
  if (accuracy >= 0.60) return "bg-amber-100/80 text-amber-700";
  return "bg-red-100/80 text-red-700";
}

function cellDot(accuracy: number | null): string {
  if (accuracy === null) return "";
  if (accuracy >= 0.85) return "bg-emerald-400";
  if (accuracy >= 0.60) return "bg-amber-400";
  return "bg-red-400";
}

function formatCell(accuracy: number | null): string {
  if (accuracy === null) return "--";
  return `${Math.round(accuracy * 100)}%`;
}

// ─── Sub-components ───

interface HeatmapCellProps {
  accuracy: number | null;
  delay: number;
  onClick: () => void;
}

const HeatmapCell = memo(function HeatmapCell({ accuracy, delay, onClick }: HeatmapCellProps) {
  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25, delay }}
      onClick={onClick}
      className={`relative flex flex-col items-center justify-center rounded-md px-1.5 py-1.5 text-[11px] font-medium leading-tight transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-forest-400 ${cellColor(accuracy)}`}
      title={accuracy !== null ? `掌握度 ${Math.round(accuracy * 100)}%` : "暂无数据"}
    >
      {accuracy !== null && (
        <span
          className={`mb-0.5 inline-block h-1.5 w-1.5 rounded-full ${cellDot(accuracy)}`}
          aria-hidden
        />
      )}
      <span>{formatCell(accuracy)}</span>
    </motion.button>
  );
});

// ─── Main component ───

interface ClassErrorHeatmapProps {
  trees: StudentTree[];
  onStudentClick?: (tree: StudentTree, focusErrorCode?: string) => void;
}

export function ClassErrorHeatmap({ trees, onStudentClick }: ClassErrorHeatmapProps) {
  const [hoveredCol, setHoveredCol] = useState<string | null>(null);

  const profileQueries = useQueries({
    queries: trees.map((tree) => ({
      queryKey: ["studentProfile", tree.student_id],
      queryFn: () => getStudentProfile(tree.student_id),
      staleTime: 60_000,
    })),
  });

  const profileMap = useMemo(() => {
    const map = new Map<string, Record<string, number>>();
    profileQueries.forEach((q, i) => {
      const profile = q.data as StudentProfile | undefined;
      if (profile?.accuracy_by_error_code) {
        map.set(trees[i].student_id, profile.accuracy_by_error_code);
      }
    });
    return map;
  }, [profileQueries, trees]);

  const columnAverages = useMemo(() => {
    const sums: Record<string, { total: number; count: number }> = {};
    for (const code of ERROR_CODES) {
      sums[code] = { total: 0, count: 0 };
    }
    for (const tree of trees) {
      const accMap = profileMap.get(tree.student_id);
      for (const code of ERROR_CODES) {
        const acc = accMap?.[code];
        if (acc !== undefined) {
          sums[code].total += acc;
          sums[code].count += 1;
        }
      }
    }
    const result: Record<string, number | null> = {};
    for (const code of ERROR_CODES) {
      result[code] = sums[code].count > 0 ? sums[code].total / sums[code].count : null;
    }
    return result;
  }, [trees, profileMap]);

  const weakestColumn = useMemo(() => {
    let minAcc = 1;
    let weakest: string | null = null;
    for (const code of ERROR_CODES) {
      const avg = columnAverages[code];
      if (avg !== null && avg < minAcc) {
        minAcc = avg;
        weakest = code;
      }
    }
    return weakest;
  }, [columnAverages]);

  const allLoaded = profileQueries.every((q) => q.isSuccess || q.isError);
  const anyLoading = !allLoaded;

  const handleCellClick = useCallback(
    (tree: StudentTree, errorCode: string) => {
      onStudentClick?.(tree, errorCode);
    },
    [onStudentClick],
  );

  return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50">
          <Grid3X3 className="h-4 w-4 text-red-500" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">错因热力图</h3>
          <p className="text-xs text-muted-foreground">精准定位全班薄弱环节 · 点击查看详情</p>
        </div>
      </div>

      {anyLoading && (
        <div className="rounded-lg border border-forest-100 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <motion.div
              className="h-3 w-3 rounded-full border-2 border-forest-300 border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
            />
            正在加载学生错因数据…
          </div>
          <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: `80px repeat(${ERROR_CODES.length}, minmax(48px, 1fr))` }}>
            <div />
            {ERROR_CODES.map((code) => (
              <div key={code} className="h-4 animate-pulse rounded bg-muted/30" />
            ))}
            <div className="h-6 animate-pulse rounded bg-muted/20" />
            {ERROR_CODES.map((code) => (
              <div key={`sk-${code}`} className="h-8 animate-pulse rounded bg-muted/20" />
            ))}
          </div>
        </div>
      )}

      {!anyLoading && (
        <div className="overflow-x-auto rounded-lg border border-forest-200/60 bg-white shadow-sm">
          <div className="min-w-[640px]">
            <div
              className="grid items-center border-b border-forest-100 bg-forest-50/30 px-2 py-2"
              style={{ gridTemplateColumns: `80px repeat(${ERROR_CODES.length}, minmax(52px, 1fr))` }}
            >
              <span className="text-[11px] font-medium text-muted-foreground">学生</span>
              {ERROR_CODES.map((code) => {
                const isWeakest = code === weakestColumn;
                const isHovered = code === hoveredCol;
                return (
                  <div
                    key={code}
                    className={`flex flex-col items-center gap-0.5 rounded px-1 py-1 text-center transition-colors ${
                      isWeakest ? "bg-red-50/70" : isHovered ? "bg-forest-50" : ""
                    }`}
                    onMouseEnter={() => setHoveredCol(code)}
                    onMouseLeave={() => setHoveredCol(null)}
                    title={ERROR_LABELS[code] ?? code}
                  >
                    <span className={`text-[11px] font-bold ${isWeakest ? "text-red-600" : "text-foreground/80"}`}>
                      {code}
                    </span>
                    <span className={`text-[9px] leading-tight ${isWeakest ? "text-red-500/70" : "text-muted-foreground/70"}`}>
                      {(ERROR_LABELS[code] ?? "").slice(0, 4)}
                    </span>
                    {isWeakest && (
                      <AlertTriangle className="mt-0.5 h-3 w-3 text-red-400" />
                    )}
                  </div>
                );
              })}
            </div>

            {trees.map((tree, rowIdx) => {
              const accMap = profileMap.get(tree.student_id);
              return (
                <motion.div
                  key={tree.student_id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: rowIdx * 0.03 }}
                  className="grid items-center border-b border-forest-50 px-2 py-1 last:border-b-0"
                  style={{ gridTemplateColumns: `80px repeat(${ERROR_CODES.length}, minmax(52px, 1fr))` }}
                >
                  <span className="truncate text-[11px] font-medium text-foreground/80" title={tree.student_name}>
                    {tree.student_name}
                  </span>
                  {ERROR_CODES.map((code, colIdx) => {
                    const accuracy = accMap?.[code] ?? null;
                    return (
                      <HeatmapCell
                        key={`${tree.student_id}-${code}`}
                        accuracy={accuracy}
                        delay={rowIdx * 0.03 + colIdx * 0.015}
                        onClick={() => handleCellClick(tree, code)}
                      />
                    );
                  })}
                </motion.div>
              );
            })}

            <div
              className="grid items-center border-t border-forest-100 bg-forest-50/20 px-2 py-2"
              style={{ gridTemplateColumns: `80px repeat(${ERROR_CODES.length}, minmax(52px, 1fr))` }}
            >
              <span className="text-[11px] font-medium text-muted-foreground">班级平均</span>
              {ERROR_CODES.map((code) => {
                const avg = columnAverages[code];
                const isWeakest = code === weakestColumn;
                return (
                  <div
                    key={`avg-${code}`}
                    className={`flex flex-col items-center rounded px-1 py-1 ${
                      isWeakest ? "bg-red-50/50" : ""
                    }`}
                  >
                    <span className={`text-[11px] font-semibold ${avg !== null ? (avg >= 0.85 ? "text-emerald-600" : avg >= 0.60 ? "text-amber-600" : "text-red-600") : "text-muted-foreground/40"}`}>
                      {formatCell(avg)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 px-1 text-[10px] text-muted-foreground">
        <span className="font-medium">掌握度：</span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-400" />
          ≥ 85% 良好
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-400" />
          60–84% 待巩固
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-red-400" />
          &lt; 60% 需关注
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-muted/40" />
          暂无数据
        </span>
        {weakestColumn && (
          <span className="ml-auto flex items-center gap-1 font-medium text-red-500">
            <AlertTriangle className="h-3 w-3" />
            最薄弱：{weakestColumn} {ERROR_LABELS[weakestColumn as ErrorCode] ?? ""}
          </span>
        )}
      </div>
    </div>
  );
}
