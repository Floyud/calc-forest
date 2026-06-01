"use client";

import { Loader2, ScanSearch, Bot, Archive, CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import type { AIGradingResult, HomeworkDetail } from "@/lib/types";
import { getErrorCodeDisplay } from "@/lib/labels";

interface StudentAnswerSimulatorProps {
  homework: HomeworkDetail | null;
  studentAnswers: Record<number, string>;
  onAnswerChange: (sequence: number, value: string) => void;
  onGrade: () => void;
  grading: boolean;
  gradingStage: "idle" | "submitting" | "grading" | "ai_grading" | "done" | "error";
  gradingError: string | null;
  gradingResult: AIGradingResult | null;
}

function accuracyTextColor(acc: number): string {
  if (acc >= 0.8) return "text-emerald-600";
  if (acc >= 0.6) return "text-amber-600";
  return "text-rose-600";
}

function buildDemoMistake(
  problem: HomeworkDetail["problems"][number],
  index: number,
): string {
  const correct = problem.correct_answer;
  const text = problem.problem;
  if (index % 5 === 1) return correct;
  if (text.includes("周长") || text.includes("半径") || text.includes("直径")) return "63.585";
  if (text.includes("面积") || text.includes("圆")) return "28.26";
  if (text.includes("比") || text.includes(":")) return correct.includes(":") ? correct.split(":").reverse().join(":") : "48";
  if (text.includes("%") || text.includes("百分")) {
    const n = Number(correct);
    return Number.isFinite(n) ? String(n * 10) : "0.35";
  }
  if (text.includes("÷") && correct.includes("/")) {
    const [n, d] = correct.split("/");
    if (n && d) return `${d}/${n}`;
  }
  if (text.includes("×") && correct.includes("/")) {
    const [n, d] = correct.split("/");
    if (n && d) return `${Number(n) + Number(d)}/${d}`;
  }
  const numeric = Number(correct);
  if (Number.isFinite(numeric)) return String(numeric + (index + 2) * 3);
  return correct;
}

export function StudentAnswerSimulator({
  homework,
  studentAnswers,
  onAnswerChange,
  onGrade,
  grading,
  gradingStage,
  gradingError,
  gradingResult,
}: StudentAnswerSimulatorProps) {
  const stageLabels: Record<string, string> = {
    idle: "准备就绪",
    submitting: "正在提交答案...",
    grading: "规则引擎批改中...",
    ai_grading: "AI 增强批改中...",
    done: "批改完成",
    error: "批改失败",
  };

  function fillSixthGradeDemoAnswers() {
    if (!homework) return;
    homework.problems.forEach((problem, index) => {
      onAnswerChange(problem.sequence, buildDemoMistake(problem, index));
    });
  }

  return (
    <div className="space-y-6">
      <Card className="surface-panel rounded-[24px] border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-warm-400" />
            学生作答预览与提交
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            模拟学生作答后提交，系统将自动进行规则批改与 AI 增强批改。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!homework ? (
            <p className="text-sm text-muted-foreground">先在左侧生成作业草案。</p>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-[18px] border border-amber-200 bg-amber-50/70 px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-amber-900">六年级错例样本</p>
                  <p className="text-xs text-amber-800/70">
                    一键填入“倒乘、百分数放大、圆公式混淆、按比分配审题”这类真实错法，方便演示批改闭环。
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={fillSixthGradeDemoAnswers}
                  className="rounded-full border-amber-300 bg-white/80 text-amber-800 hover:bg-white"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  填入六年级错例
                </Button>
              </div>

              {homework.problems.map((problem) => (
                <div
                  key={problem.id}
                  className="rounded-[18px] border border-[color:var(--tone-line)] bg-forest-50/30 p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        第 {problem.sequence} 题
                      </p>
                      <p className="mt-1 text-base text-foreground">{problem.problem}</p>
                    </div>
                    <Badge
                      variant="outline"
                      className="border-[color:var(--tone-line)] text-[var(--tone-muted)]"
                    >
                      {getErrorCodeDisplay(problem.target_error_code)}
                    </Badge>
                  </div>
                  <Textarea
                    className="mt-3 min-h-20"
                    placeholder="模拟学生写在空白处的答案或简短过程"
                    value={studentAnswers[problem.sequence] ?? ""}
                    onChange={(e) => onAnswerChange(problem.sequence, e.target.value)}
                  />
                </div>
              ))}

              <Button
                onClick={onGrade}
                disabled={grading || homework.status === "draft"}
                className="rounded-full bg-[var(--tone-accent-strong)] text-white hover:bg-[color:color-mix(in_oklab,var(--tone-accent-strong)_88%,black)]"
              >
                {grading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ScanSearch className="mr-2 h-4 w-4" />
                )}
                提交并批改
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="surface-panel rounded-[24px] border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-warm-400" />
            批改进度
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            流程：提交答案 → 规则批改 → AI 增强批改
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {gradingStage === "idle" && !gradingResult && (
            <p className="text-sm text-muted-foreground">
              提交答案后这里会显示批改进度与结果。
            </p>
          )}

          {gradingStage !== "idle" && (
            <div className="grid gap-3 md:grid-cols-3">
              {[
                { label: "提交答案", stage: "submitting" },
                { label: "规则批改", stage: "grading" },
                { label: "AI 批改", stage: "ai_grading" },
              ].map(({ label, stage }) => {
                const stages = ["submitting", "grading", "ai_grading"];
                const currentIdx = stages.indexOf(gradingStage);
                const stageIdx = stages.indexOf(stage);
                const isDone = gradingStage === "done" || currentIdx > stageIdx;
                const isActive = gradingStage === stage;
                const isError = gradingStage === "error" && isActive;

                return (
                  <div
                    key={stage}
                    className="rounded-[18px] border border-[color:var(--tone-line)] bg-forest-50/30 p-3"
                  >
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <Badge
                      className={`mt-2 ${
                        isError
                          ? "bg-rose-50 text-rose-700 ring-1 ring-rose-200"
                          : isDone
                            ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
                            : isActive
                              ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
                              : "bg-[var(--tone-soft)] text-[var(--tone-ink)] ring-1 ring-[color:var(--tone-line)]"
                      }`}
                    >
                      {isError ? "失败" : isDone ? "已完成" : isActive ? stageLabels[gradingStage] : "等待中"}
                    </Badge>
                  </div>
                );
              })}
            </div>
          )}

          {gradingError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
              {gradingError}
            </div>
          )}

          {gradingResult && (
            <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-forest-50/30 p-4">
              <div className="flex items-center gap-2 text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-xs uppercase tracking-[0.2em]">批改结果</span>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">准确率</p>
                  <p className={`text-2xl font-bold ${accuracyTextColor(gradingResult.accuracy)}`}>
                    {Math.round(gradingResult.accuracy * 100)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">正确/总题数</p>
                  <p className="text-lg font-semibold text-foreground">
                    {gradingResult.correct_count}/{gradingResult.total_problems}
                  </p>
                </div>
              </div>
              {gradingResult.primary_errors.length > 0 && (
                <p className="mt-2 text-sm text-muted-foreground">
                  主错因：{gradingResult.primary_errors.join(", ")}
                </p>
              )}
              {gradingResult.next_suggestion && (
                <p className="mt-1 text-sm text-muted-foreground">
                  建议：{gradingResult.next_suggestion}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {gradingResult && (
        <Card className="surface-panel rounded-[24px] border-0 shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Archive className="h-4 w-4 text-forest-600" />
              批改记录
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-forest-50/30 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm text-foreground">
                    作业 {gradingResult.homework_id}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    学生 {gradingResult.student_id}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className="bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">
                    已批改
                  </Badge>
                  {gradingResult.review_status && (
                    <Badge
                      className={
                        gradingResult.review_status === "pending_teacher_review"
                          ? "bg-sky-50 text-sky-700 ring-1 ring-sky-200"
                          : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
                      }
                    >
                      {gradingResult.review_status === "pending_teacher_review"
                        ? "待教师审核"
                        : "已审核"}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
