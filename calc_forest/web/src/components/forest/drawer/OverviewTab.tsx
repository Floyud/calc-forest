"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, Minus, AlertTriangle,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StudentTree, WeakKnowledgePoint } from "@/lib/types";
import { ERROR_LABELS, GROWTH_STAGES } from "@/lib/types";

const AccuracyTrendChart = dynamic(
  () => import("../AccuracyTrendChart").then((m) => ({ default: m.AccuracyTrendChart })),
  { ssr: false },
);

const ErrorRadarChart = dynamic(
  () => import("../ErrorRadarChart").then((m) => ({ default: m.ErrorRadarChart })),
  { ssr: false },
);

function getStageLabel(stage: string): string {
  const found = GROWTH_STAGES.find((s) => s.key === stage);
  return found ? found.label : "播种";
}

function TrendIcon({ current, previous }: { current: number; previous: number }) {
  const diff = current - previous;
  if (diff > 0.05) return <TrendingUp className="h-4 w-4 text-forest-600" />;
  if (diff < -0.05) return <TrendingDown className="h-4 w-4 text-volcano-400" />;
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

function accuracyBadgeColor(acc: number): string {
  if (acc >= 0.8) return "bg-forest-100 text-forest-700 border-forest-200";
  if (acc >= 0.6) return "bg-warm-100 text-warm-700 border-warm-200";
  return "bg-volcano-100 text-volcano-500 border-volcano-200";
}

const GRADE_LABELS: Record<number, string> = {
  1: "一年级", 2: "二年级", 3: "三年级",
  4: "四年级", 5: "五年级", 6: "六年级",
};

function getGradeLabel(grade: number): string {
  return GRADE_LABELS[grade] ?? `${grade}年级`;
}

function WeakKnowledgeCard({ point }: { point: WeakKnowledgePoint }) {
  const borderColor =
    point.mastery_zone === "needs_practice"
      ? "border-l-red-400"
      : "border-l-amber-400";

  const zoneEmoji = point.mastery_zone === "needs_practice" ? "🔴" : "🟡";

  const accPct = point.accuracy != null ? Math.round(point.accuracy * 100) : null;
  const barColor =
    point.accuracy != null
      ? point.accuracy >= 0.6
        ? "bg-warm-400"
        : "bg-red-400"
      : "bg-gray-300";

  return (
    <div className={`rounded-lg border border-parchment-300 border-l-4 ${borderColor} bg-white p-3.5`}>
      <div className="flex items-center gap-2">
        <span className="text-xs">{zoneEmoji}</span>
        <Badge variant="outline" className="border-volcano-300 text-volcano-500 text-[10px] px-1.5">
          {point.error_code}
        </Badge>
        <span className="text-sm font-medium text-ink-500">
          {ERROR_LABELS[point.error_code as keyof typeof ERROR_LABELS] ?? point.error_code}
        </span>
      </div>

      {point.typical_error && (
        <div className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
          <span>典型错误：{point.typical_error}</span>
        </div>
      )}

      <div className="mt-2.5 flex items-center gap-2.5">
        <span className="text-[11px] text-muted-foreground shrink-0">
          准确率
        </span>
        <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-parchment-200">
          {accPct != null && (
            <div
              className={`absolute left-0 top-0 h-full rounded-full ${barColor}`}
              style={{ width: `${accPct}%` }}
            />
          )}
        </div>
        <span className="text-xs font-medium text-ink-400 shrink-0 w-8 text-right">
          {accPct != null ? `${accPct}%` : "--"}
        </span>
        <span className="text-[10px] text-muted-foreground shrink-0">
          ({point.total_attempts}次练习)
        </span>
      </div>
    </div>
  );
}

interface OverviewTabProps {
  tree: StudentTree;
  errorAccuracyMap: Record<string, number>;
  totalDiagnoses: number;
  weakPoints: WeakKnowledgePoint[];
  studentInfo: {
    name: string;
    grade: number;
    class_id: string;
    student_number: string;
    personality_tags?: string[];
    learning_style?: string;
    notes?: string;
    guidance_mode?: string;
    id: string;
    textbook_version: string;
    start_grade: number;
    enrolled_at: string;
  } | null;
  masteryData: {
    error_codes: Record<string, {
      mastery_probability: number;
      zone: string;
      total_attempts: number;
      correct_count: number;
    }>;
    overall_mastery: number;
    mastered_count: number;
    total_error_codes: number;
  } | null | undefined;
  lastWeek: { accuracy: number } | undefined;
  firstWeek: { accuracy: number } | undefined;
  overallTrend: number;
}

export function OverviewTab({
  tree,
  errorAccuracyMap,
  totalDiagnoses,
  weakPoints,
  studentInfo,
  masteryData,
  lastWeek,
  firstWeek,
  overallTrend,
}: OverviewTabProps) {
  const sortedWeakPoints = useMemo(
    () =>
      weakPoints
        .filter((p) => p.mastery_zone !== "mastered")
        .sort((a, b) => (a.accuracy ?? 0) - (b.accuracy ?? 0))
        .slice(0, 5),
    [weakPoints],
  );

  return (
    <motion.div
      key="overview"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      className="space-y-6"
    >
      {studentInfo && (
        <div className="flex items-center justify-between rounded-lg border border-parchment-300 bg-white px-4 py-3">
          <div>
            <h3 className="text-base font-bold text-ink-500">{studentInfo.name}</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {getGradeLabel(studentInfo.grade)} · {studentInfo.class_id}班{studentInfo.student_number ? ` · 学号${studentInfo.student_number}` : ""}
            </p>
          </div>
          <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${accuracyBadgeColor(tree.overall_accuracy)}`}>
            {Math.round(tree.overall_accuracy * 100)}%
          </span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <Card size="sm">
          <CardContent className="pt-3 text-center">
            <p className={`text-2xl font-bold ${tree.overall_accuracy >= 0.8 ? "text-forest-600" : tree.overall_accuracy >= 0.6 ? "text-warm-500" : "text-volcano-400"}`}>
              {Math.round(tree.overall_accuracy * 100)}%
            </p>
            <p className="text-xs text-muted-foreground">总准确率</p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="pt-3 text-center">
            <p className="text-2xl font-bold text-ink-500">{tree.correct_count}/{tree.total_attempts}</p>
            <p className="text-xs text-muted-foreground">正确/总题</p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="pt-3 text-center">
            <p className="text-2xl font-bold text-ink-500">{tree.days_completed}</p>
            <p className="text-xs text-muted-foreground">练习天数</p>
          </CardContent>
        </Card>
      </div>

      {tree.encouragement_needed && (
        <div className="rounded-lg border border-volcano-200 bg-volcano-50 p-3">
          <p className="text-sm font-medium text-volcano-500">
            这个小朋友最近遇到了困难，准确率在下降。多一些耐心和鼓励，帮他重新找回节奏。
          </p>
        </div>
      )}

      <div>
        <h3 className="mb-2 text-sm font-medium text-ink-500">趋势</h3>
        <div className="flex items-center gap-2">
          <TrendIcon current={lastWeek?.accuracy ?? 0} previous={firstWeek?.accuracy ?? 0} />
          <span className="text-sm">
            {overallTrend > 0.05 ? "持续进步中" : overallTrend < -0.05 ? "需要关注" : "保持稳定"}
          </span>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium text-ink-500">错因能力图谱</h3>
        <p className="mb-2 text-xs text-muted-foreground">
          基于 {totalDiagnoses} 次诊断记录 · 虚线为60%危险线
        </p>
        <ErrorRadarChart accuracyByErrorCode={errorAccuracyMap} />
      </div>

      {masteryData && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-ink-500">掌握度总览</h3>
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">总体掌握度</span>
                <span className="font-medium text-ink-500">
                  {Math.round(masteryData.overall_mastery * 100)}%
                </span>
              </div>
              <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-parchment-300">
                <motion.div
                  className="absolute left-0 top-0 h-full rounded-full bg-forest-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${masteryData.overall_mastery * 100}%` }}
                  transition={{ delay: 0.2, duration: 0.7 }}
                />
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                已掌握 {masteryData.mastered_count} / {masteryData.total_error_codes} 个错因类型
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {([
                {
                  zone: "mastered" as const,
                  label: "已掌握",
                  emoji: "🟢",
                  bgClass: "bg-forest-50 border-forest-200",
                  textClass: "text-forest-700",
                },
                {
                  zone: "learning" as const,
                  label: "学习中",
                  emoji: "🟡",
                  bgClass: "bg-warm-50 border-warm-200",
                  textClass: "text-warm-700",
                },
                {
                  zone: "needs_practice" as const,
                  label: "需练习",
                  emoji: "🔴",
                  bgClass: "bg-volcano-50 border-volcano-200",
                  textClass: "text-volcano-500",
                },
              ] as const).map(({ zone, label, emoji, bgClass, textClass }) => {
                const codes = Object.entries(masteryData.error_codes)
                  .filter(([, v]) => v.zone === zone)
                  .map(([code]) => code);
                if (codes.length === 0) return null;
                return (
                  <div
                    key={zone}
                    className={`rounded-lg border p-2.5 ${bgClass}`}
                  >
                    <div className="flex items-center gap-1">
                      <span className="text-xs">{emoji}</span>
                      <span className={`text-xs font-medium ${textClass}`}>
                        {label}
                      </span>
                      <span className={`ml-auto text-xs font-bold ${textClass}`}>
                        {codes.length}
                      </span>
                    </div>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {codes.map((code) => (
                        <span
                          key={code}
                          className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-medium ${textClass} bg-white/60`}
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {sortedWeakPoints.length > 0 && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-volcano-400" />
            <h3 className="text-sm font-medium text-ink-500">薄弱知识点</h3>
            <span className="text-[11px] text-muted-foreground">按准确率升序</span>
          </div>
          <div className="space-y-2.5">
            {sortedWeakPoints.map((point) => (
              <WeakKnowledgeCard key={`${point.error_code}-${point.unit_id}`} point={point} />
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="mb-3 text-sm font-medium text-ink-500">周准确率变化</h3>
        <AccuracyTrendChart data={tree.weekly_accuracy} />
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium text-ink-500">作业周历</h3>
        <div className="grid grid-cols-8 gap-1.5">
          {tree.weekly_accuracy.map((w) => {
            const acc = w.accuracy;
            let bg = "bg-volcano-100 text-volcano-500";
            if (acc >= 0.8) bg = "bg-forest-100 text-forest-700";
            else if (acc >= 0.6) bg = "bg-warm-100 text-warm-500";
            return (
              <div key={w.week_number} className={`flex flex-col items-center rounded-md p-1.5 text-xs ${bg}`}>
                <span className="font-medium">W{w.week_number}</span>
                <span>{Math.round(acc * 100)}%</span>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium text-ink-500">成长进度</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{tree.days_completed} / {tree.total_days} 天</span>
            <span className="font-medium">{getStageLabel(tree.current_stage)}</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-parchment-300">
            <motion.div
              className="absolute left-0 top-0 h-full rounded-full bg-forest-500"
              initial={{ width: 0 }}
              animate={{ width: `${(tree.days_completed / tree.total_days) * 100}%` }}
              transition={{ delay: 0.3, duration: 0.8 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
