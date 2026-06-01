"use client";

import { useCallback, useEffect, useState } from "react";
import { BarChart3, TrendingUp, FileText, AlertCircle, Loader2, Award, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ClassHomeworkAnalytics } from "@/lib/types";
import { getClassHomeworkAnalytics } from "@/lib/api";
import { DEFAULT_CLASS_ID } from "@/lib/config";
import { getErrorCodeDisplay, getStatusLabel } from "@/lib/labels";
import { EChartsBase } from "@/components/ui/echarts-base";
import type { EChartsOption } from "echarts";

const DEMO_ANALYTICS: ClassHomeworkAnalytics = {
  class_id: DEFAULT_CLASS_ID,
  total_homeworks: 18,
  avg_accuracy: 0.68,
  completion_rate: 0.94,
  most_common_error: "E05",
  error_distribution: {
    E05: 34,
    E06: 28,
    E10: 21,
    E09: 15,
    E11: 9,
  },
  recent_homeworks: [
    { homework_id: "DEMO-0612", created_at: "2026-05-12", problem_count: 6, submission_count: 32, avg_accuracy: 0.61, top_error: "E05", status: "graded" },
    { homework_id: "DEMO-0615", created_at: "2026-05-15", problem_count: 6, submission_count: 31, avg_accuracy: 0.66, top_error: "E06", status: "graded" },
    { homework_id: "DEMO-0618", created_at: "2026-05-18", problem_count: 8, submission_count: 32, avg_accuracy: 0.72, top_error: "E10", status: "graded" },
    { homework_id: "DEMO-0621", created_at: "2026-05-21", problem_count: 6, submission_count: 30, avg_accuracy: 0.69, top_error: "E05", status: "graded" },
    { homework_id: "DEMO-0624", created_at: "2026-05-24", problem_count: 8, submission_count: 32, avg_accuracy: 0.77, top_error: "E09", status: "graded" },
  ],
};

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-forest-200 bg-forest-50/30 p-4">
      <div className={`rounded-lg p-2 ${accent}`}>
        <Icon className="h-4 w-4 text-white" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-bold text-foreground">{value}</p>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </div>
    </div>
  );
}

export function HomeworkAnalytics() {
  const [data, setData] = useState<ClassHomeworkAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingDemoData, setUsingDemoData] = useState(false);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getClassHomeworkAnalytics(DEFAULT_CLASS_ID, 10);
      const sparseOrUnreasonable =
        result.demo_mode ||
        result.total_homeworks === 0 ||
        (result.avg_accuracy <= 0.05 && result.completion_rate <= 0.05) ||
        result.recent_homeworks.some(
          (homework) => homework.submission_count === 0 || homework.avg_accuracy <= 0,
        );
      setData(sparseOrUnreasonable && !result.demo_mode ? DEMO_ANALYTICS : result);
      setUsingDemoData(sparseOrUnreasonable);
    } catch (err) {
      if (err instanceof Error && err.message.includes("404")) {
        setData(DEMO_ANALYTICS);
        setUsingDemoData(true);
      } else {
        setError(err instanceof Error ? err.message : "加载分析数据失败");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-forest-600" />
        <span className="ml-3 text-sm text-muted-foreground">加载分析数据...</span>
      </div>
    );
  }

  if (error === "analytics_unavailable") {
    return (
      <Card className="border-forest-200 bg-white text-foreground shadow-sm">
        <CardContent className="py-16 text-center">
          <BarChart3 className="mx-auto h-10 w-10 text-forest-300" />
          <p className="mt-4 text-sm font-medium text-foreground">作业分析功能即将上线</p>
          <p className="mt-1 text-xs text-muted-foreground">
            后端分析接口正在开发中，完成后将自动展示班级作业数据统计。
          </p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-rose-200 bg-rose-50 text-foreground shadow-sm">
        <CardContent className="flex items-start gap-3 py-6">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-500" />
          <div>
            <p className="text-sm font-medium text-rose-700">加载失败</p>
            <p className="mt-1 text-xs text-rose-600">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const accPct = Math.round(data.avg_accuracy * 100);
  const compPct = Math.round(data.completion_rate * 100);

  const errorEntries = Object.entries(data.error_distribution).sort(
    ([, a], [, b]) => b - a,
  );
  const maxErrorCount = errorEntries.length > 0 ? errorEntries[0][1] : 1;

  const errorChartOption: EChartsOption | null = (() => {
    if (!data) return null;
    const entries = Object.entries(data.error_distribution).sort(
      ([, a], [, b]) => b - a,
    );
    if (entries.length === 0) return null;
    // ECharts draws y-axis bottom→top; reverse so largest appears at top
    const reversed = [...entries].reverse();
    const maxVal = entries[0][1];
    return {
      grid: { top: 4, right: 48, bottom: 4, left: 80 },
      xAxis: {
        type: "value",
        show: false,
        max: maxVal * 1.2,
      },
      yAxis: {
        type: "category",
        data: reversed.map(([code]) => getErrorCodeDisplay(code)),
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: "bar",
          data: reversed.map(([, count]) => count),
          barWidth: 18,
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: [
                { offset: 0, color: "#5a9e4e" },
                { offset: 1, color: "#46803c" },
              ],
            },
          },
          label: {
            show: true,
            position: "right",
            fontSize: 12,
            fontWeight: 600 as const,
            color: "#244220",
          },
        },
      ],
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
      },
    };
  })();

  const trendChartOption: EChartsOption | null = (() => {
    if (!data || data.recent_homeworks.length < 2) return null;
    const homeworks = [...data.recent_homeworks].reverse();
    return {
      grid: { top: 32, right: 16, bottom: 28, left: 48 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(255,255,255,0.96)",
        borderColor: "#e5e0d4",
        textStyle: { color: "#244220", fontSize: 12 },
        formatter: (params: unknown) => {
          const p = Array.isArray(params) ? params[0] : params;
          const idx = (p as { dataIndex?: number }).dataIndex ?? 0;
          const hw = homeworks[idx];
          if (!hw) return "";
          const acc = Math.round(hw.avg_accuracy * 100);
          const errInfo = hw.top_error ? getErrorCodeDisplay(hw.top_error) : "无";
          return `<div style="font-weight:600;margin-bottom:4px">${hw.created_at}</div>` +
            `<div>准确率：<b>${acc}%</b></div>` +
            `<div>提交：${hw.submission_count} 人</div>` +
            `<div>主要错因：${errInfo}</div>`;
        },
      },
      xAxis: {
        type: "category",
        data: homeworks.map((hw) => hw.created_at.slice(5)),
        axisLabel: { fontSize: 11, color: "#8b8570" },
        axisLine: { lineStyle: { color: "#e5e0d4" } },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: { formatter: "{value}%", fontSize: 11, color: "#8b8570" },
        splitLine: { lineStyle: { color: "#f0ebe0", type: "dashed" } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: "line",
          data: homeworks.map((hw) => Math.round(hw.avg_accuracy * 100)),
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#46803c", width: 2.5 },
          itemStyle: { color: "#46803c", borderWidth: 2, borderColor: "#fff" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(70,128,60,0.20)" },
                { offset: 1, color: "rgba(70,128,60,0.01)" },
              ],
            },
          },
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#c4a87c", type: "dashed", width: 1 },
            data: [{ yAxis: 80, label: { formatter: "优秀线 80%", fontSize: 10, color: "#8b8570" } }],
          },
        },
      ],
    };
  })();

  const rankingData = (() => {
    if (!data || data.recent_homeworks.length === 0) return null;
    const sorted = [...data.recent_homeworks].sort(
      (a, b) => b.avg_accuracy - a.avg_accuracy,
    );
    const top3 = sorted.slice(0, 3);
    const bottom3 = sorted.slice(-3).reverse();
    return { top3, bottom3 };
  })();

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={FileText}
          label="作业总数"
          value={String(data.total_homeworks)}
          accent="bg-forest-600"
        />
        <StatCard
          icon={TrendingUp}
          label="平均准确率"
          value={`${accPct}%`}
          sub={accPct >= 80 ? "表现优秀" : accPct >= 60 ? "仍有提升空间" : "需要关注"}
          accent={accPct >= 80 ? "bg-emerald-600" : accPct >= 60 ? "bg-amber-500" : "bg-rose-500"}
        />
        <StatCard
          icon={BarChart3}
          label="完成率"
          value={`${compPct}%`}
          accent="bg-sky-600"
        />
        <StatCard
          icon={AlertCircle}
          label="最常见错因"
          value={data.most_common_error ? getErrorCodeDisplay(data.most_common_error) : "暂无"}
          accent="bg-amber-500"
        />
      </div>

      {usingDemoData && (
        <div className="rounded-[18px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          当前展示竞赛演示用合成分析数据；后端接口可用后会自动切换为真实班级统计。
        </div>
      )}

      <Card className="surface-panel rounded-[24px] border-0 text-foreground shadow-none">
        <CardHeader>
          <CardTitle className="text-base">近期作业记录</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_homeworks.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              暂无作业记录
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-forest-200 text-left">
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">日期</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">题量</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">提交</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">准确率</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">主要错因</th>
                    <th className="pb-2 font-medium text-muted-foreground">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_homeworks.map((hw) => (
                    <tr key={hw.homework_id} className="border-b border-forest-100 last:border-0">
                      <td className="py-2.5 pr-4 text-foreground">{hw.created_at}</td>
                      <td className="py-2.5 pr-4">{hw.problem_count}</td>
                      <td className="py-2.5 pr-4">{hw.submission_count}</td>
                      <td className="py-2.5 pr-4">
                        <span
                          className={
                            hw.avg_accuracy >= 0.8
                              ? "text-emerald-600"
                              : hw.avg_accuracy >= 0.6
                                ? "text-amber-600"
                                : "text-rose-600"
                          }
                        >
                          {Math.round(hw.avg_accuracy * 100)}%
                        </span>
                      </td>
                      <td className="py-2.5 pr-4">
                        {hw.top_error ? getErrorCodeDisplay(hw.top_error) : "—"}
                      </td>
                      <td className="py-2.5">
                        <Badge
                          className={
                            hw.status === "archived" || hw.status === "graded"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-forest-100 text-forest-700"
                          }
                        >
                          {getStatusLabel(hw.status)}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {errorEntries.length > 0 && (
        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">错因分布</CardTitle>
          </CardHeader>
          <CardContent>
            {errorChartOption && (
              <EChartsBase
                option={errorChartOption}
                className="w-full"
                style={{ height: `${Math.max(errorEntries.length * 30 + 16, 60)}px` }}
              />
            )}
          </CardContent>
        </Card>
      )}

      {trendChartOption && (
        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardHeader className="flex flex-row items-center gap-2">
            <TrendingUp className="h-4 w-4 text-forest-600" />
            <CardTitle className="text-base">班级趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <EChartsBase
              option={trendChartOption}
              className="w-full"
              style={{ height: "260px" }}
            />
          </CardContent>
        </Card>
      )}

      {rankingData && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader className="flex flex-row items-center gap-2">
              <ArrowUpRight className="h-4 w-4 text-emerald-600" />
              <CardTitle className="text-base">最佳表现</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {rankingData.top3.map((hw, i) => {
                const pct = Math.round(hw.avg_accuracy * 100);
                return (
                  <div key={hw.homework_id} className="flex items-center gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <p className="truncate text-sm font-medium text-foreground">{hw.created_at}</p>
                        <span className="text-sm font-bold text-emerald-600">{pct}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-emerald-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader className="flex flex-row items-center gap-2">
              <ArrowDownRight className="h-4 w-4 text-amber-600" />
              <CardTitle className="text-base">需要关注</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {rankingData.bottom3.map((hw) => {
                const pct = Math.round(hw.avg_accuracy * 100);
                return (
                  <div key={hw.homework_id} className="flex items-center gap-3">
                    <Award className="h-6 w-6 shrink-0 text-amber-400" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <p className="truncate text-sm font-medium text-foreground">{hw.created_at}</p>
                        <span className="text-sm font-bold text-amber-600">{pct}%</span>
                      </div>
                      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-amber-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-amber-300 to-amber-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      {hw.top_error && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          主要错因：{getErrorCodeDisplay(hw.top_error)}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
