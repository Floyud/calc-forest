"use client";

import { CheckCircle2, AlertTriangle, Check, Pencil } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MarkdownContent } from "@/components/ui/markdown-content";
import type { AIGradingResult } from "@/lib/types";

interface GradingResultProps {
  gradingResult: AIGradingResult | null;
  completionSummary: string | null;
}

function accuracyColor(acc: number): string {
  if (acc >= 0.8) return "bg-emerald-500";
  if (acc >= 0.6) return "bg-amber-500";
  return "bg-rose-500";
}

function accuracyTextColor(acc: number): string {
  if (acc >= 0.8) return "text-emerald-600";
  if (acc >= 0.6) return "text-amber-600";
  return "text-rose-600";
}

export function GradingResult({ gradingResult, completionSummary }: GradingResultProps) {
  if (!gradingResult) {
    return (
      <Card className="surface-panel rounded-[24px] border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CheckCircle2 className="h-4 w-4 text-forest-600" />
            批改结果
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            提交并完成批改后，结果将在此显示。
          </p>
        </CardContent>
      </Card>
    );
  }

  const accPct = Math.round(gradingResult.accuracy * 100);

  return (
    <Card className="surface-panel rounded-[24px] border-0 shadow-none">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CheckCircle2 className="h-4 w-4 text-forest-600" />
          批改结果
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between rounded-[18px] border border-[color:var(--tone-line)] bg-forest-50/30 p-4">
          <div>
            <p className="text-xs text-muted-foreground">总体准确率</p>
            <p className={`text-2xl font-bold ${accuracyTextColor(gradingResult.accuracy)}`}>{accPct}%</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">正确/总题数</p>
            <p className="text-lg font-semibold text-foreground">
              {gradingResult.correct_count}/{gradingResult.total_problems}
            </p>
          </div>
        </div>

        {completionSummary && (
          <div className="rounded-[18px] border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-center gap-2 text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              <span className="font-medium">批改摘要</span>
            </div>
            <div className="mt-2 text-sm text-foreground">
              <MarkdownContent content={completionSummary} className="[&_p]:text-sm [&_p]:text-foreground [&_p]:mb-1 last:[&_p]:mb-0" />
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              主错因：{gradingResult.primary_errors.join(", ") || "无"}
            </p>
            {gradingResult.next_suggestion && (
              <p className="mt-1 text-sm text-muted-foreground">
                建议：{gradingResult.next_suggestion}
              </p>
            )}
          </div>
        )}

        {accPct < 60 && (
          <div className="flex items-start gap-3 rounded-[18px] border border-rose-200 bg-rose-50 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-500" />
            <div>
              <p className="text-sm font-medium text-rose-700">需要关注</p>
              <p className="mt-1 text-xs text-rose-600">
                准确率低于 60%，建议进行针对性辅导。
              </p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">教师确认</p>
          <div className="flex gap-2">
            <Button size="sm" className="rounded-full bg-emerald-600 text-white hover:bg-emerald-500">
              <Check className="mr-1 h-3.5 w-3.5" />
              确认批改
            </Button>
            <Button size="sm" variant="outline" className="rounded-full border-amber-300 text-amber-700 hover:bg-amber-50">
              <Pencil className="mr-1 h-3.5 w-3.5" />
              修改
            </Button>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <Badge
              className={
                gradingResult.review_status === "pending_teacher_review"
                  ? "bg-sky-50 text-sky-700 ring-1 ring-sky-200"
                  : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
              }
            >
              {gradingResult.review_status === "pending_teacher_review" ? "待教师审核" : "已审核"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
