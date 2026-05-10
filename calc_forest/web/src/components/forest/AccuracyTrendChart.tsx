"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { WeeklyAccuracy } from "@/lib/types";

interface AccuracyTrendChartProps {
  data: WeeklyAccuracy[];
}

export function AccuracyTrendChart({ data }: AccuracyTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        暂无数据
      </div>
    );
  }

  const chartData = data.map((w) => ({
    name: `W${w.week_number}`,
    accuracy: Math.round(w.accuracy * 100),
    total: w.total_attempts,
  }));

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.92 0.01 260)" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "oklch(0.85 0.02 260)" }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip
            formatter={(value: unknown) => [`${value}%`, "准确率"]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid oklch(0.88 0.05 160)",
            }}
          />
          <ReferenceLine
            y={80}
            stroke="oklch(0.65 0.15 160)"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
          />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="oklch(0.55 0.15 160)"
            strokeWidth={2.5}
            dot={{ fill: "oklch(0.50 0.15 160)", strokeWidth: 0, r: 3 }}
            activeDot={{ r: 5, fill: "oklch(0.45 0.18 160)" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
