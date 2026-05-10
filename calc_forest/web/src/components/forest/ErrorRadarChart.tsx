"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const RADAR_LABELS: Record<string, string> = {
  E01: "基础事实",
  E02: "进位",
  E03: "退位",
  E04: "数位对齐",
  E05: "运算顺序",
  E06: "小数分数",
  E07: "抄写",
  E08: "步骤遗漏",
  E09: "符号混淆",
  E10: "估算",
  E11: "未验算",
};

const ALL_CODES = [
  "E01", "E02", "E03", "E04", "E05", "E06",
  "E07", "E08", "E09", "E10", "E11",
];

interface ErrorRadarChartProps {
  accuracyByErrorCode: Record<string, number>;
}

interface ChartDatum {
  code: string;
  label: string;
  accuracy: number;
  hasData: boolean;
  danger: number;
}

function accuracyColor(acc: number): string {
  if (acc >= 80) return "oklch(0.50 0.15 160)";
  if (acc >= 60) return "oklch(0.72 0.13 85)";
  return "oklch(0.60 0.18 30)";
}

function RadarTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDatum }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;

  return (
    <div
      style={{
        fontSize: 12,
        borderRadius: 8,
        border: "1px solid oklch(0.88 0.05 160)",
        background: "white",
        padding: "8px 12px",
        boxShadow: "0 2px 8px oklch(0.90 0.02 260 / 0.5)",
      }}
    >
      <p style={{ fontWeight: 600, color: "oklch(0.25 0.03 260)" }}>
        {d.code} · {d.label}
      </p>
      {d.hasData ? (
        <p style={{ color: accuracyColor(d.accuracy), marginTop: 2 }}>
          准确率 {d.accuracy}%
        </p>
      ) : (
        <p style={{ color: "oklch(0.60 0.02 260)", marginTop: 2 }}>
          暂无数据
        </p>
      )}
    </div>
  );
}

export function ErrorRadarChart({ accuracyByErrorCode }: ErrorRadarChartProps) {
  const data: ChartDatum[] = ALL_CODES.map((code) => {
    const raw = accuracyByErrorCode[code];
    return {
      code,
      label: RADAR_LABELS[code],
      accuracy: raw != null ? Math.round(raw * 100) : 0,
      hasData: raw != null,
      danger: 60,
    };
  });

  const hasAnyData = data.some((d) => d.hasData);

  if (!hasAnyData) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        暂无错因诊断数据
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="68%" data={data}>
          <PolarGrid stroke="oklch(0.90 0.02 260)" />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: "oklch(0.45 0.03 260)" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            ticks={[0, 60, 100]}
            tick={{ fontSize: 9, fill: "oklch(0.65 0.02 260)" }}
            tickFormatter={(v: number) => `${v}%`}
            axisLine={false}
          />
          <Tooltip content={<RadarTooltip />} />

          {/* Danger zone reference hexagon at 60% */}
          <Radar
            name="危险线"
            dataKey="danger"
            stroke="oklch(0.65 0.12 30)"
            fill="transparent"
            fillOpacity={0}
            strokeWidth={1}
            strokeDasharray="4 3"
            strokeOpacity={0.35}
            isAnimationActive={false}
          />

          {/* Main accuracy radar */}
          <Radar
            name="准确率"
            dataKey="accuracy"
            stroke="oklch(0.50 0.15 160)"
            fill="oklch(0.55 0.15 160)"
            fillOpacity={0.18}
            strokeWidth={2}
            dot={{
              r: 3,
              fill: "oklch(0.45 0.15 160)",
              stroke: "white",
              strokeWidth: 1,
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
