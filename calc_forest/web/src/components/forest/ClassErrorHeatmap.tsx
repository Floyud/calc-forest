"use client";

import { useMemo, useCallback } from "react";
import { useQueries } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, Grid3X3 } from "lucide-react";
import { getStudentProfile } from "@/lib/api";
import type { StudentTree, ErrorCode, StudentProfile } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";
import type { EChartsOption } from "echarts";
import { EChartsBase } from "@/components/ui/echarts-base";

// ─── Error codes displayed in heatmap columns ───

const ERROR_CODES: ErrorCode[] = [
  "E01", "E02", "E03", "E04", "E05",
  "E06", "E07", "E08", "E09", "E10", "E11",
];

// Sentinel value for null/missing data in ECharts heatmap
const NULL_VAL = -1;

// ─── Main component ───

interface ClassErrorHeatmapProps {
  trees: StudentTree[];
  onStudentClick?: (tree: StudentTree, focusErrorCode?: string) => void;
}

export function ClassErrorHeatmap({ trees, onStudentClick }: ClassErrorHeatmapProps) {
  const profileQueries = useQueries({
    queries: trees.map((tree) => ({
      queryKey: ["studentProfile", tree.student_id],
      queryFn: () => getStudentProfile(tree.student_id),
      staleTime: 5 * 60 * 1000,
      enabled: !!tree.student_id && tree.student_id.length > 0,
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

  // ─── Build heatmap data and category arrays ───

  const yCategories = useMemo(
    () => [...trees.map((t) => t.student_name), "班级平均"],
    [trees],
  );

  const heatmapData = useMemo(() => {
    const points: [number, number, number][] = [];

    trees.forEach((tree, yIdx) => {
      const accMap = profileMap.get(tree.student_id);
      ERROR_CODES.forEach((code, xIdx) => {
        const acc = accMap?.[code];
        points.push([xIdx, yIdx, acc != null ? acc : NULL_VAL]);
      });
    });

    // Average row
    const avgY = trees.length;
    ERROR_CODES.forEach((code, xIdx) => {
      const avg = columnAverages[code];
      points.push([xIdx, avgY, avg !== null ? avg : NULL_VAL]);
    });

    return points;
  }, [trees, profileMap, columnAverages]);

  // ─── ECharts option (memoised) ───

  const chartOption = useMemo(() => {
    const weak = weakestColumn;

    return {
      tooltip: {
        formatter(params: Record<string, unknown>) {
          const d = params.data as [number, number, number] | undefined;
          if (!d) return "";
          const [xIdx, yIdx, val] = d;
          const code = ERROR_CODES[xIdx];
          const name = yCategories[yIdx];
          const label = ERROR_LABELS[code as ErrorCode] ?? code;
          if (val === NULL_VAL) {
            return `<b>${name}</b><br/>${code} ${label}<br/><span style="color:#94a3b8">暂无数据</span>`;
          }
          const pct = Math.round(val * 100);
          const color = val >= 0.85 ? "#047857" : val >= 0.6 ? "#b45309" : "#b91c1c";
          return `<b>${name}</b><br/>${code} ${label}<br/>掌握度: <b style="color:${color}">${pct}%</b>`;
        },
      },
      grid: {
        top: 44,
        right: 12,
        bottom: 8,
        left: 12,
        containLabel: true,
      },
      xAxis: {
        type: "category" as const,
        data: ERROR_CODES,
        position: "top" as const,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "#e2e8f0" } },
        axisLabel: {
          fontSize: 10,
          interval: 0,
          color(value?: string | number) {
            return value === weak ? "#dc2626" : "#64748b";
          },
          fontWeight(value?: string | number) {
            return value === weak ? "bold" : "normal";
          },
          formatter(value?: string | number) {
            const v = String(value ?? "");
            const short = (ERROR_LABELS[v as ErrorCode] ?? "").slice(0, 4);
            return `${v}\n${short}`;
          },
        },
      },
      yAxis: {
        type: "category" as const,
        data: yCategories,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "#e2e8f0" } },
        axisLabel: {
          fontSize: 11,
          color(value?: string | number) {
            return value === "班级平均" ? "#64748b" : "#334155";
          },
          fontWeight(value?: string | number) {
            return value === "班级平均" ? 500 : "normal";
          },
        },
      },
      visualMap: {
        show: false,
        type: "piecewise" as const,
        pieces: [
          { value: NULL_VAL, color: "#f1f5f9" },
          { gte: 0, lt: 0.6, color: "#fecaca" },
          { gte: 0.6, lt: 0.85, color: "#fde68a" },
          { gte: 0.85, lte: 1, color: "#bbf7d0" },
        ],
      },
      series: [
        {
          type: "heatmap" as const,
          data: heatmapData,
          label: {
            show: true,
            fontSize: 10,
            fontWeight: 500,
            formatter(params: Record<string, unknown>) {
              const d = params.data as [number, number, number] | undefined;
              if (!d) return "";
              const val = d[2];
              if (val === NULL_VAL) return "--";
              return `${Math.round(val * 100)}%`;
            },
            color(params: Record<string, unknown>) {
              const d = params.data as [number, number, number] | undefined;
              if (!d) return "#94a3b8";
              const val = d[2];
              if (val === NULL_VAL) return "#94a3b8";
              if (val >= 0.85) return "#047857";
              if (val >= 0.6) return "#b45309";
              return "#b91c1c";
            },
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 8,
              shadowColor: "rgba(0,0,0,0.15)",
            },
          },
          itemStyle: {
            borderColor: "#fff",
            borderWidth: 2,
            borderRadius: 4,
          },
        },
      ],
    };
  }, [heatmapData, yCategories, weakestColumn]);

  // ─── Chart click → onStudentClick ───

  const handleChartClick = useCallback(
    (params: Record<string, unknown>) => {
      if (!onStudentClick) return;
      const d = params.data as [number, number, number] | undefined;
      if (!d) return;
      const [, yIdx] = d;
      // Ignore clicks on the average row
      if (yIdx >= trees.length) return;
      const xIdx = d[0];
      const errorCode = ERROR_CODES[xIdx];
      const tree = trees[yIdx];
      onStudentClick(tree, errorCode);
    },
    [onStudentClick, trees],
  );

  // ─── Render ───

  const chartHeight = Math.max(200, (trees.length + 1) * 36 + 16);

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
        <div className="overflow-hidden rounded-lg border border-forest-200/60 bg-white shadow-sm">
          <EChartsBase
            option={chartOption as unknown as EChartsOption}
            onClick={handleChartClick}
            className="w-full"
            style={{ height: `${chartHeight}px` }}
          />
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
