"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { LogOut, Target, TrendingUp, TreePine, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import { logger } from "@/lib/logger";

const EChartsBase = dynamic(
  () => import("@/components/ui/echarts-base").then((m) => ({ default: m.EChartsBase })),
  { ssr: false },
);

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

const STAGE_EMOJI: Record<string, string> = {
  seed: "🌱", sprout: "🌿", seedling: "🌳",
  young_tree: "🌲", mature_tree: "🏔️",
  flowering: "🌸", fruiting: "🍎", ancient: "🏡", towering: "🌲",
};

const STAGE_LABEL: Record<string, string> = {
  seed: "种子", sprout: "嫩芽", seedling: "小树苗",
  young_tree: "年轻树", mature_tree: "大树",
  flowering: "开花", fruiting: "结果", ancient: "古树", towering: "参天大树",
};

interface GrowthData {
  student: { id: string; name: string; grade: number };
  growth_summary: { stage: string; days_completed: number; tree_species: string | null };
  weak_areas: Array<{ error_code: string; label: string; accuracy: number; total_attempts: number }>;
  recent_results: Array<{ homework_id: string; date: string; correct: number; total: number; accuracy: number }>;
}

function TreeSVG({ stage, size = 160 }: { stage: string; size?: number }) {
  const growth = stageProgress(stage);
  const trunkH = 20 + growth * 60;
  const canopyR = 15 + growth * 35;
  const leaves = Math.floor(3 + growth * 8);

  return (
    <svg width={size} height={size} viewBox="0 0 160 160">
      <rect x="0" y="0" width="160" height="160" fill="transparent" />
      <ellipse cx="80" cy={160 - trunkH - canopyR * 0.6} rx={canopyR} ry={canopyR * 0.85}
        fill="var(--color-sage-300)" opacity="0.7" />
      {Array.from({ length: leaves }).map((_, i) => {
        const angle = (i / leaves) * Math.PI * 2;
        const r = canopyR * (0.5 + Math.random() * 0.4);
        const cx = 80 + Math.cos(angle) * r * 0.6;
        const cy = 160 - trunkH - canopyR * 0.5 + Math.sin(angle) * r * 0.5;
        const leafR = 6 + Math.random() * 8;
        return (
          <circle key={i} cx={cx} cy={cy} r={leafR}
            fill={i % 2 === 0 ? "var(--color-sage-400)" : "var(--color-sage-300)"} opacity="0.8" />
        );
      })}
      <rect x="76" y={160 - trunkH} width="8" height={trunkH} rx="3" fill="var(--color-sand-400)" />
      {growth > 0.3 && (
        <circle cx="95" cy={160 - trunkH - canopyR * 0.3} r="5" fill="var(--color-sand-300)" opacity="0.9" />
      )}
      {growth > 0.6 && (
        <>
          <circle cx="68" cy={160 - trunkH - canopyR * 0.5} r="4" fill="var(--color-blush-300)" opacity="0.8" />
          <circle cx="88" cy={160 - trunkH - canopyR * 0.7} r="3.5" fill="var(--color-blush-200)" opacity="0.7" />
        </>
      )}
    </svg>
  );
}

function stageProgress(stage: string): number {
  const order = ["seed", "sprout", "seedling", "young_tree", "mature_tree", "flowering", "fruiting", "ancient", "towering"];
  const idx = order.indexOf(stage);
  return idx >= 0 ? idx / (order.length - 1) : 0;
}

export default function StudentGrowthPage() {
  const router = useRouter();
  const [student, setStudent] = useState<{ id: string; name: string } | null>(null);
  const [data, setData] = useState<GrowthData | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("student_session");
    if (!raw) { router.push("/s/login"); return; }
    const session = JSON.parse(raw);
    setStudent(session.student);

    fetch(`${API_BASE}/api/students/${session.student.id}/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch((err) => { logger.error("growth_fetch_failed", { error: String(err) }); });
  }, [router]);

  const trendOption = useMemo(() => {
    if (!data?.recent_results?.length) return null;
    const results = [...data.recent_results].reverse();
    return {
      grid: { top: 30, right: 16, bottom: 30, left: 40 },
      xAxis: {
        type: "category" as const,
        data: results.map((r) => r.date?.slice(5) || ""),
        axisLabel: { fontSize: 11, color: "#b0a899" },
        axisLine: { lineStyle: { color: "#e8e4de" } },
      },
      yAxis: {
        type: "value" as const,
        min: 0, max: 100,
        axisLabel: { fontSize: 11, color: "#b0a899", formatter: "{value}%" },
        splitLine: { lineStyle: { color: "#f3f1ed" } },
      },
      series: [{
        type: "line" as const,
        data: results.map((r) => r.accuracy),
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#9baac8", width: 3 },
        itemStyle: { color: "#9baac8" },
        areaStyle: { color: { type: "linear" as const, x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(155, 170, 200, 0.25)" }, { offset: 1, color: "rgba(155, 170, 200, 0.02)" }] } },
      }],
      tooltip: { trigger: "axis" as const },
    };
  }, [data]);

  const radarOption = useMemo(() => {
    if (!data?.weak_areas?.length) return null;
    return {
      radar: {
        indicator: data.weak_areas.map((w) => ({ name: w.error_code, max: 100 })),
        radius: "65%",
        axisName: { color: "#b0a899", fontSize: 11 },
        splitArea: { areaStyle: { color: ["rgba(155, 170, 200, 0.04)", "rgba(155, 170, 200, 0.08)"] } },
      },
      series: [{
        type: "radar" as const,
        data: [{ value: data.weak_areas.map((w) => Math.round(w.accuracy * 100)), areaStyle: { color: "rgba(155, 170, 200, 0.18)" }, lineStyle: { color: "#9baac8" }, itemStyle: { color: "#9baac8" } }],
      }],
    };
  }, [data]);

  if (!student) return null;

  const stage = data?.growth_summary?.stage || "seed";
  const days = data?.growth_summary?.days_completed || 0;
  const progress = stageProgress(stage);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold flex items-center gap-2" style={{ color: "#3e3a36" }}>
          <TreePine className="w-5 h-5" style={{ color: "var(--color-mist-400)" }} /> 我的成长
        </h1>
        <button
          onClick={() => { localStorage.removeItem("student_session"); router.push("/s/login"); }}
          className="text-xs flex items-center gap-1 transition-colors duration-300"
          style={{ color: "var(--color-soft-400)" }}
        >
          <LogOut className="w-3 h-3" /> 退出
        </button>
      </div>

      <div className="surface-soft rounded-2xl p-6 text-center">
        <div className="flex justify-center">
          <TreeSVG stage={stage} />
        </div>
        <p className="text-lg font-semibold mt-2" style={{ color: "#3e3a36" }}>{student.name} 的计算树</p>
        <p className="text-sm mt-1" style={{ color: "var(--color-mist-400)" }}>
          {STAGE_LABEL[stage] || "种子"} · {STAGE_EMOJI[stage] || "🌱"}
        </p>
        <div className="mt-3 max-w-xs mx-auto">
          <div className="flex justify-between text-xs mb-1" style={{ color: "var(--color-soft-400)" }}>
            <span>成长进度</span>
            <span>{Math.round(progress * 100)}%</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--color-soft-100)" }}>
            <div className="h-full rounded-full progress-fill"
              style={{
                width: `${progress * 100}%`,
                background: "linear-gradient(90deg, var(--color-mist-300) 0%, var(--color-mist-400) 100%)",
              }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="surface-double-bezel rounded-xl p-4 text-center">
          <Trophy className="w-5 h-5 mx-auto mb-1" style={{ color: "var(--color-sand-400)" }} />
          <p className="text-xl font-semibold" style={{ color: "#3e3a36" }}>{days}</p>
          <p className="text-xs" style={{ color: "var(--color-soft-400)" }}>坚持天数</p>
        </div>
        <div className="surface-double-bezel rounded-xl p-4 text-center">
          <Target className="w-5 h-5 mx-auto mb-1" style={{ color: "var(--color-mist-400)" }} />
          <p className="text-xl font-semibold" style={{ color: "#3e3a36" }}>
            {data?.recent_results?.length ? Math.round(data.recent_results.reduce((s, r) => s + r.accuracy, 0) / data.recent_results.length) : 0}%
          </p>
          <p className="text-xs" style={{ color: "var(--color-soft-400)" }}>近期正确率</p>
        </div>
        <div className="surface-double-bezel rounded-xl p-4 text-center">
          <TrendingUp className="w-5 h-5 mx-auto mb-1" style={{ color: "var(--color-mist-300)" }} />
          <p className="text-xl font-semibold" style={{ color: "#3e3a36" }}>
            {data?.recent_results?.length || 0}
          </p>
          <p className="text-xs" style={{ color: "var(--color-soft-400)" }}>完成作业</p>
        </div>
      </div>

      {trendOption && (
        <div className="surface-soft rounded-2xl p-4">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: "#3e3a36" }}>
            <TrendingUp className="w-4 h-4" style={{ color: "var(--color-mist-400)" }} /> 正确率趋势
          </h2>
          <div className="h-48">
            <EChartsBase option={trendOption} className="h-full w-full" />
          </div>
        </div>
      )}

      {radarOption && (
        <div className="surface-soft rounded-2xl p-4">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-1.5" style={{ color: "#3e3a36" }}>
            <Target className="w-4 h-4" style={{ color: "var(--color-mist-400)" }} /> 薄弱环节分析
          </h2>
          <div className="h-56">
            <EChartsBase option={radarOption} className="h-full w-full" />
          </div>
        </div>
      )}

      {data?.weak_areas?.length ? (
        <div className="surface-soft rounded-2xl p-4">
          <h2 className="text-sm font-semibold mb-3" style={{ color: "#3e3a36" }}>错因详情</h2>
          <div className="space-y-3">
            {data.weak_areas.map((w) => {
              const pct = Math.round(w.accuracy * 100);
              return (
                <div key={w.error_code}>
                  <div className="flex justify-between text-sm mb-1">
                    <span style={{ color: "var(--color-soft-500)" }}>{w.error_code} · {w.label}</span>
                    <span className={cn("font-semibold",
                      pct >= 80 ? "text-sage-400" : pct >= 60 ? "text-sand-400" : "text-blush-400"
                    )}>
                      {pct}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--color-soft-100)" }}>
                    <div
                      className={cn("h-full rounded-full")}
                      style={{
                        width: `${pct}%`,
                        background: pct >= 80
                          ? "linear-gradient(90deg, var(--color-sage-300), var(--color-sage-400))"
                          : pct >= 60
                            ? "linear-gradient(90deg, var(--color-sand-300), var(--color-sand-400))"
                            : "linear-gradient(90deg, var(--color-blush-300), var(--color-blush-400))",
                      }}
                    />
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: "var(--color-soft-400)" }}>练习 {w.total_attempts} 次</p>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {data?.recent_results?.length ? (
        <div className="surface-soft rounded-2xl p-4">
          <h2 className="text-sm font-semibold mb-3" style={{ color: "#3e3a36" }}>近期作业</h2>
          <div className="space-y-2">
            {data.recent_results.map((r) => (
              <div key={r.homework_id} className="flex items-center justify-between py-2 last:border-0"
                style={{ borderBottom: "1px solid rgba(180, 172, 158, 0.1)" }}>
                <div>
                  <p className="text-sm" style={{ color: "var(--color-soft-500)" }}>{r.date}</p>
                  <p className="text-xs" style={{ color: "var(--color-soft-400)" }}>{r.correct}/{r.total} 正确</p>
                </div>
                <span className="text-sm font-semibold px-2 py-0.5 rounded-lg"
                  style={{
                    background: r.accuracy >= 80
                      ? "var(--color-sage-100)"
                      : r.accuracy >= 60
                        ? "var(--color-sand-100)"
                        : "var(--color-blush-100)",
                    color: r.accuracy >= 80
                      ? "var(--color-sage-500)"
                      : r.accuracy >= 60
                        ? "var(--color-sand-500)"
                        : "var(--color-blush-500)",
                  }}>
                  {r.accuracy}%
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="text-center text-sm py-4" style={{ color: "var(--color-mist-400)" }}>
        {days === 0 ? "开始你的计算森林之旅吧！" : days < 7 ? "坚持就是胜利，继续加油！" : days < 30 ? "你真的很棒，树苗在茁壮成长！" : "你是计算森林的主人，大树参天！"}
      </div>
    </div>
  );
}
