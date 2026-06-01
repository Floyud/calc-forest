"use client";

import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { EChartsBase } from "@/components/ui/echarts-base";

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

function accuracyColor(acc: number): string {
  if (acc >= 80) return "#16a34a";
  if (acc >= 60) return "#ca8a04";
  return "#dc2626";
}

export function ErrorRadarChart({ accuracyByErrorCode }: ErrorRadarChartProps) {
  const { activeCodes, option } = useMemo(() => {
    const codes = ALL_CODES.filter((code) => accuracyByErrorCode[code] != null);

    const indicators = codes.map((code) => ({
      name: `${RADAR_LABELS[code]}`,
      max: 100,
    }));

    const values = codes.map((code) => Math.round(accuracyByErrorCode[code] * 100));

    const chartOption: EChartsOption = {
      tooltip: {
        trigger: "item",
        formatter: (params: unknown) => {
          const p = params as { data?: { value?: number[] }; name?: string };
          if (!p.data?.value) return "";
          const idx = codes.indexOf(
            ALL_CODES.find((c) => RADAR_LABELS[c] === p.name) ?? "",
          );
          if (idx === -1) return "";
          const code = codes[idx];
          const label = RADAR_LABELS[code];
          const val = p.data.value[idx];
          const color = accuracyColor(val);
          return `<div style="font-size:12px;padding:2px 0">
            <strong style="color:#1e293b">${code} · ${label}</strong><br/>
            <span style="color:${color}">安全率 ${val}%</span>
          </div>`;
        },
      },
      radar: {
        indicator: indicators,
        shape: "polygon",
        radius: "68%",
        axisName: {
          color: "#64748b",
          fontSize: 10,
        },
        splitArea: {
          show: false,
        },
        splitLine: {
          lineStyle: {
            color: "#e2e8f0",
          },
        },
        axisLine: {
          lineStyle: {
            color: "#e2e8f0",
          },
        },
      },
      series: [
        {
          type: "radar",
          symbol: "circle",
          symbolSize: 6,
          data: [
            {
              name: "危险线",
              value: codes.map(() => 60),
              lineStyle: {
                type: "dashed",
                color: "#b45309",
                opacity: 0.35,
                width: 1,
              },
              areaStyle: {
                opacity: 0,
              },
              itemStyle: {
                opacity: 0,
              },
            },
            {
              name: "安全率",
              value: values,
              lineStyle: {
                color: "#22c55e",
                width: 2,
              },
              areaStyle: {
                color: "#22c55e",
                opacity: 0.18,
              },
              itemStyle: {
                color: "#15803d",
                borderColor: "#fff",
                borderWidth: 1,
              },
            },
          ],
        },
      ],
    };

    return { activeCodes: codes, option: chartOption };
  }, [accuracyByErrorCode]);

  if (activeCodes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        暂无错因诊断数据
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <EChartsBase option={option} />
    </div>
  );
}
