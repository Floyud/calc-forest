"use client";

import { ClipboardCheck, CheckCircle2, Edit3, Loader2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { HomeworkDetail } from "@/lib/types";
import { getStatusLabel, getErrorCodeDisplay } from "@/lib/labels";
import { getStatusTone } from "@/lib/presentation";

const DIFFICULTY_STYLES: Record<string, { border: string; badge: string; label: string }> = {
  A: { border: "border-l-blue-500", badge: "bg-blue-100 text-blue-700", label: "基础" },
  B: { border: "border-l-amber-500", badge: "bg-amber-100 text-amber-700", label: "中档" },
  C: { border: "border-l-rose-500", badge: "bg-rose-100 text-rose-700", label: "高档" },
};

interface ProblemPreviewProps {
  homework: HomeworkDetail;
  reviewApproved: boolean;
  onApproveReview: () => void;
  onAssign: () => void;
  assigning: boolean;
}

export function ProblemPreview({
  homework,
  reviewApproved,
  onApproveReview,
  onAssign,
  assigning,
}: ProblemPreviewProps) {
  const difficultyCounts = homework.problems.reduce<Record<string, number>>((acc, problem) => {
    acc[problem.difficulty] = (acc[problem.difficulty] ?? 0) + 1;
    return acc;
  }, {});
  const difficultySummary = ["A", "B", "C"]
    .filter((level) => (difficultyCounts[level] ?? 0) > 0)
    .map((level) => `${level} ${difficultyCounts[level]}`)
    .join(" · ");

  return (
    <Card className="surface-panel rounded-[24px] border-0 shadow-none">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-forest-600" />
            作业草案预览
          </CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={getStatusTone(homework.status)}>
              {getStatusLabel(homework.status)}
            </Badge>
            <Badge variant="outline" className="border-[color:var(--tone-line)] text-[var(--tone-muted)]">
              作业 {homework.id}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div
          className={`flex flex-wrap items-center justify-between gap-3 rounded-[18px] border p-3 ${
            reviewApproved
              ? "border-emerald-200 bg-emerald-50/50"
              : "border-amber-200 bg-amber-50/50"
          }`}
        >
          <div className="flex items-center gap-2">
            <Badge
              className={
                reviewApproved
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-amber-100 text-amber-700"
              }
            >
              {reviewApproved ? "已审核" : "待教师审核"}
            </Badge>
            <span className="text-xs text-muted-foreground">
              错因：{homework.error_codes_target.join(", ") || "自动推断"}
            </span>
          </div>
          <div className="flex gap-2">
            {!reviewApproved && (
              <Button
                size="sm"
                onClick={onApproveReview}
                className="rounded-full bg-emerald-600 text-white hover:bg-emerald-500"
              >
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                审核通过
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              disabled
              className="rounded-full border-[color:var(--tone-line)] bg-white/80 text-[var(--tone-muted)]"
            >
              <Edit3 className="mr-1 h-3.5 w-3.5" />
              编辑题目
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onAssign}
              disabled={assigning || !reviewApproved || homework.status === "assigned" || homework.status === "in_progress"}
              className="rounded-full border-[color:var(--tone-line)] bg-white/80 text-[var(--tone-ink)] hover:bg-white disabled:opacity-50"
            >
              {assigning ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <ClipboardCheck className="mr-1 h-3.5 w-3.5" />
              )}
              {homework.status === "assigned" || homework.status === "in_progress" ? "已布置" : "布置作业"}
            </Button>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-white/70 px-4 py-3">
            <p className="text-xs text-muted-foreground">年级定位</p>
            <p className="mt-1 text-sm font-semibold text-[var(--tone-ink)]">六年级综合计算</p>
          </div>
          <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-white/70 px-4 py-3">
            <p className="text-xs text-muted-foreground">难度结构</p>
            <p className="mt-1 text-sm font-semibold text-[var(--tone-ink)]">
              {difficultySummary || "待生成"}
            </p>
          </div>
          <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-white/70 px-4 py-3">
            <p className="text-xs text-muted-foreground">审核动作</p>
            <p className="mt-1 text-sm font-semibold text-[var(--tone-ink)]">
              {reviewApproved ? "可布置给学生" : "先确认题目与错因"}
            </p>
          </div>
        </div>

        <Separator className="bg-forest-200" />

        <div className="space-y-3">
          {homework.problems.map((problem) => {
            const diffStyle = DIFFICULTY_STYLES[problem.difficulty] ?? DIFFICULTY_STYLES.A;
            return (
              <div key={problem.id} className={`rounded-[18px] border border-l-4 border-forest-200 bg-forest-50/30 p-4 ${diffStyle.border}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-forest-100 text-xs font-semibold text-forest-700">
                        {problem.sequence}
                      </span>
                      <span className="text-base font-medium leading-relaxed text-foreground">{problem.problem}</span>
                    </div>
                    {problem.knowledge_point && (
                      <p className="mt-1.5 pl-8 text-xs text-muted-foreground">
                        {problem.knowledge_point}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-2">
                    <Badge variant="outline" className="border-[color:var(--tone-line)] text-xs text-[var(--tone-muted)]">
                      {getErrorCodeDisplay(problem.target_error_code)}
                    </Badge>
                    <Badge className={`text-[10px] ${diffStyle.badge}`}>
                      {diffStyle.label}
                    </Badge>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-[var(--tone-soft)]/70 p-3">
          <p className="text-xs text-muted-foreground">
            知识点：{homework.knowledge_points.join(" / ") || "待推断"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
