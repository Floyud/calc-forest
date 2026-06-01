"use client";

import { useMemo, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DEFAULT_CLASS_ID } from "@/lib/config";
import type {
  AIGradingResult,
  DifficultyStrategy,
  ExerciseType,
  HomeworkDetail,
  HomeworkGenerateRequest,
} from "@/lib/types";
import {
  aiGradeHomework,
  assignHomework,
  generateHomework,
  getHomeworkDetail,
  getHomeworkSubmissions,
  gradeHomework,
  submitHomework,
} from "@/lib/api";
import { getStatusLabel } from "@/lib/labels";
import { getReviewTone } from "@/lib/presentation";
import { HomeworkForm } from "@/components/homework/HomeworkForm";
import { ProblemPreview } from "@/components/homework/ProblemPreview";
import { GradingResult } from "@/components/homework/GradingResult";
import { HomeworkAnalytics } from "@/components/homework/HomeworkAnalytics";
import { StudentAnswerSimulator } from "@/components/homework/StudentAnswerSimulator";
import {
  InsightStrip,
  PageHero,
  ReviewStatusBadge,
  SectionPanel,
  WorkspacePage,
} from "@/components/layout/workspace-shell";

const DEFAULT_FORM: HomeworkGenerateRequest = {
  class_id: DEFAULT_CLASS_ID,
  student_id: "S001",
  grade: 6,
  error_codes_target: ["E05", "E06", "E09", "E10"],
  problem_count: 6,
  difficulty: "C",
};

const DEFAULT_EXERCISE_TYPES: ExerciseType[] = [
  "脱式计算",
  "分数运算",
  "比与比例",
  "图形计算",
];

type GradingStage = "idle" | "submitting" | "grading" | "ai_grading" | "done" | "error";

export default function HomeworkPage() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [selectedExerciseTypes, setSelectedExerciseTypes] = useState<ExerciseType[]>(DEFAULT_EXERCISE_TYPES);
  const [difficultyStrategy, setDifficultyStrategy] = useState<DifficultyStrategy>("C");
  const [loading, setLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [grading, setGrading] = useState(false);
  const [homework, setHomework] = useState<HomeworkDetail | null>(null);
  const [studentAnswers, setStudentAnswers] = useState<Record<number, string>>({});
  const [gradingResult, setGradingResult] = useState<AIGradingResult | null>(null);
  const [gradingStage, setGradingStage] = useState<GradingStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [gradingError, setGradingError] = useState<string | null>(null);
  const [reviewApproved, setReviewApproved] = useState(false);

  const completionSummary = useMemo(() => {
    if (!gradingResult) return null;
    return `${gradingResult.correct_count}/${gradingResult.total_problems} 正确，准确率 ${Math.round(gradingResult.accuracy * 100)}%`;
  }, [gradingResult]);

  async function handleGenerate() {
    setError(null);
    setFormError(null);
    setLoading(true);
    setHomework(null);
    setGradingResult(null);
    setGradingStage("idle");
    setGradingError(null);
    setReviewApproved(false);

    try {
      const payload = {
        ...form,
        exercise_types: selectedExerciseTypes,
        difficulty_strategy: difficultyStrategy,
        difficulty:
          difficultyStrategy === "auto" || difficultyStrategy === "mixed"
            ? "B"
            : difficultyStrategy,
      };
      const generated = await generateHomework(payload);
      const detail = await getHomeworkDetail(generated.homework_id);
      setHomework(detail);
      setStudentAnswers(Object.fromEntries(detail.problems.map((problem) => [problem.sequence, ""])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成作业失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleAssign() {
    if (!homework) return;
    setAssigning(true);
    setError(null);
    try {
      await assignHomework(homework.id);
      const detail = await getHomeworkDetail(homework.id);
      setHomework(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "布置作业失败");
    } finally {
      setAssigning(false);
    }
  }

  async function handleGrade() {
    if (!homework) return;
    setGrading(true);
    setError(null);
    setGradingError(null);
    setGradingResult(null);

    try {
      // Step 1: Submit answers
      setGradingStage("submitting");
      await submitHomework({
        homework_id: homework.id,
        student_id: form.student_id ?? "S001",
        answers: studentAnswers,
      });

      // Step 2: Rule-based grading
      setGradingStage("grading");
      const gradeResult = await gradeHomework(homework.id, form.student_id ?? "S001");

      // Step 3: AI enhanced grading (optional, may fail gracefully)
      let aiResult: AIGradingResult | null = null;
      setGradingStage("ai_grading");
      try {
        aiResult = await aiGradeHomework(homework.id, DEFAULT_CLASS_ID);
      } catch {
        // AI grading is optional; fall back to rule-based result
        aiResult = {
          homework_id: gradeResult.homework_id,
          student_id: gradeResult.student_id,
          total_problems: gradeResult.total_problems,
          correct_count: gradeResult.correct_count,
          accuracy: gradeResult.accuracy,
          primary_errors: gradeResult.primary_errors,
          next_suggestion: gradeResult.next_suggestion,
          profile_updated: gradeResult.profile_updated,
          growth_updated: gradeResult.growth_updated,
        };
      }

      setGradingResult(aiResult);
      setGradingStage("done");

      // Refresh homework detail to get updated status
      try {
        const detail = await getHomeworkDetail(homework.id);
        setHomework(detail);
      } catch {
        // non-critical
      }
    } catch (err) {
      setGradingStage("error");
      setGradingError(err instanceof Error ? err.message : "批改失败");
    } finally {
      setGrading(false);
    }
  }

  function handleAnswerChange(sequence: number, value: string) {
    setStudentAnswers((prev) => ({ ...prev, [sequence]: value }));
  }

  const pendingReview = !reviewApproved || gradingResult?.review_status === "pending_teacher_review";

  return (
    <WorkspacePage>
      <PageHero
        eyebrow="作业生成、提交、批改、审核"
        title="AI 批阅，教师把关。"
        description="生成个性化作业草案，学生提交答案后由规则引擎与 AI 双重批改，最终通过教师审核门。"
        metric={{
          label: "审核状态",
          value: pendingReview ? "待教师审核" : "教师已确认",
          note: homework ? `当前作业：${homework.id}` : "先生成一份个性化作业草案",
        }}
        aside={
          <div className="space-y-3">
            <ReviewStatusBadge status={pendingReview ? "pending" : "reviewed"} />
            <InsightStrip
              title="工作流"
              value="生成草案 → 学生作答 → 提交批改 → 教师确认"
              detail="规则引擎负责判对错，AI 负责辅助总结与说明。"
            />
            <InsightStrip
              title="当前任务"
              value={homework ? "完成布置并提交作答" : "先配置目标错因与难度策略"}
              detail={
                gradingStage === "done"
                  ? "批改已完成，等待教师审核"
                  : gradingStage !== "idle"
                    ? "批改进行中..."
                    : "还没有进入批改阶段"
              }
              tone="warn"
            />
            <InsightStrip
              title="合规边界"
              value="所有输出默认 pending_teacher_review"
              detail="教师审核通过后，系统建议才进入正式生效状态。"
            />
          </div>
        }
      />

      <SectionPanel
        title="教师批阅工作台"
        description="左侧配置作业，中间看题目与作答过程，右侧查看批改与审核结果。"
      >
        <Tabs defaultValue="generate" className="space-y-6">
          <TabsList className="rounded-full bg-[var(--tone-soft)] p-1">
            <TabsTrigger
              value="generate"
              className="rounded-full px-4 data-active:bg-white data-active:text-[var(--tone-ink)]"
            >
              生成与批阅
            </TabsTrigger>
            <TabsTrigger
              value="analytics"
              className="rounded-full px-4 data-active:bg-white data-active:text-[var(--tone-ink)]"
            >
              作业分析
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate">
            <div className="grid gap-6 xl:grid-cols-[0.9fr_1fr_0.9fr]">
              <HomeworkForm
                form={form}
                onFormChange={setForm}
                selectedExerciseTypes={selectedExerciseTypes}
                onExerciseTypesChange={setSelectedExerciseTypes}
                difficultyStrategy={difficultyStrategy}
                onDifficultyStrategyChange={setDifficultyStrategy}
                onGenerate={handleGenerate}
                loading={loading}
                error={error}
                formError={formError}
              />

              <div className="space-y-6">
                {homework ? (
                  <ProblemPreview
                    homework={homework}
                    reviewApproved={reviewApproved}
                    onApproveReview={() => setReviewApproved(true)}
                    onAssign={handleAssign}
                    assigning={assigning}
                  />
                ) : (
                  <SectionPanel
                    title="作业草案预览"
                    description="生成后，这里会展示题目结构、知识点和待审核状态。"
                    className="h-full"
                  >
                    <div className="paper-grid rounded-[20px] border border-dashed border-[color:var(--tone-line)] bg-white/60 px-4 py-10 text-center">
                      <ShieldCheck className="mx-auto h-8 w-8 text-[var(--tone-accent-strong)]" />
                      <p className="mt-3 text-sm text-muted-foreground">先在左侧配置参数并生成作业草案。</p>
                    </div>
                  </SectionPanel>
                )}

                <StudentAnswerSimulator
                  homework={homework}
                  studentAnswers={studentAnswers}
                  onAnswerChange={handleAnswerChange}
                  onGrade={handleGrade}
                  grading={grading}
                  gradingStage={gradingStage}
                  gradingError={gradingError}
                  gradingResult={gradingResult}
                />
              </div>

              <div className="space-y-6">
                <GradingResult
                  gradingResult={gradingResult}
                  completionSummary={completionSummary}
                />
                <SectionPanel
                  title="审核提醒"
                  description="系统负责先行整理，老师负责最后确认。"
                  contentClassName="space-y-3"
                >
                  <div className={`rounded-[18px] px-4 py-3 ${getReviewTone(pendingReview ? "pending_teacher_review" : "reviewed")}`}>
                    <p className="text-sm font-medium">{pendingReview ? "仍需教师审核" : "已完成教师确认"}</p>
                    <p className="mt-1 text-xs opacity-80">
                      {pendingReview
                        ? "请在布置和归档前确认题目、错因与批改摘要。"
                        : "这份作业已经符合当前教师端演示流程。"}
                    </p>
                  </div>
                  <InsightStrip
                    title="批改状态"
                    value={gradingResult ? `${getStatusLabel("graded")} / ${gradingStage === "done" ? "AI 批改完成" : "待批改"}` : "尚未开始"}
                    detail="便于老师快速判断是否需要等待批改完成后再审核。"
                  />
                </SectionPanel>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analytics">
            <HomeworkAnalytics />
          </TabsContent>
        </Tabs>
      </SectionPanel>

      <SectionPanel
        title="流程边界说明"
        description="这部分帮助后续前端继续保持统一调性。"
      >
        <div className="grid gap-3 md:grid-cols-3">
          <InsightStrip
            title="规则引擎"
            value="算术对错只由规则判断"
            detail="不把 LLM 用作最终对错判断器。"
          />
          <InsightStrip
            title="教师角色"
            value="审核是必经步骤"
            detail="所有 AI 输出先进入待教师审核态。"
            tone="warn"
          />
          <InsightStrip
            title="学生端边界"
            value="本轮只做教师演示"
            detail="学生完整作答体验仍保持受控预览，而不是独立 App。"
          />
        </div>
      </SectionPanel>
    </WorkspacePage>
  );
}
