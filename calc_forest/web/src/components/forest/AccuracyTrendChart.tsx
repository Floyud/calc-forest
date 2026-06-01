"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { EChartsBase } from "@/components/ui/echarts-base";
import type { WeeklyAccuracy } from "@/lib/types";

interface AccuracyTrendChartProps {
  data: WeeklyAccuracy[];
}

export function AccuracyTrendChart({ data }: AccuracyTrendChartProps) {
  const option = useMemo<EChartsOption>(() => {
    const weeks = data.map((w) => `W${w.week_number}`);
    const accuracies = data.map((w) => Math.round(w.accuracy * 100));
    const refLine = data.map(() => 80);

    return {
      grid: { top: 10, right: 15, left: 35, bottom: 20 },
      xAxis: {
        type: "category",
        data: weeks,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "oklch(0.85 0.02 260)" } },
        axisLabel: { fontSize: 11 },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: { fontSize: 11, formatter: "{value}%" },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: { type: "dashed", color: "oklch(0.92 0.01 260)" },
        },
      },
      tooltip: {
        trigger: "axis",
        formatter: (params: unknown) => {
          const p = (params as { value: number }[])[0];
          return `准确率: ${p.value}%`;
        },
      },
      series: [
        {
          type: "line",
          data: accuracies,
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "oklch(0.55 0.15 160)", width: 2.5 },
          itemStyle: { color: "oklch(0.50 0.15 160)" },
          emphasis: {
            itemStyle: {
              color: "oklch(0.45 0.18 160)",
              borderWidth: 2,
              borderColor: "#fff",
            },
            scale: true,
          },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "oklch(0.65 0.12 160 / 0.35)" },
                { offset: 1, color: "oklch(0.65 0.12 160 / 0.02)" },
              ],
            },
          },
        },
        {
          type: "line",
          data: refLine,
          smooth: false,
          symbol: "none",
          lineStyle: {
            color: "oklch(0.65 0.15 160)",
            type: "dashed",
            width: 1,
            opacity: 0.5,
          },
          tooltip: { show: false },
        },
      ],
    };
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        暂无数据
      </div>
    );
  }

  return (
    <div className="h-48 w-full">
      <EChartsBase option={option} />
    </div>
  );
}
