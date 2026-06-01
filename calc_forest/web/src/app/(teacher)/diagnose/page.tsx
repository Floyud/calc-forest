"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  ClipboardList,
  Lightbulb,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DifySessionDraftResponse, DifySessionDraftRequest, GuidanceMode } from "@/lib/types";
import { API_BASE, DEFAULT_STUDENT_ID } from "@/lib/config";
import PipelineProgress from "@/components/diagnose/PipelineProgress";
import { MarkdownContent } from "@/components/ui/markdown-content";

const VerticalCalcAnimation = dynamic(
  () =>
    import("@/components/guidance/VerticalCalcAnimation").then(
      (m) => m.VerticalCalcAnimation,
    ),
  { ssr: false },
);

type DemoExample = {
  label: string;
  grade: number;
  problem: string;
  correct: string;
  student: string;
  steps?: string;
};

const DEMO_EXAMPLES: DemoExample[] = [
  {
    label: "分数混合 (含括号)",
    grade: 6,
    problem: "(3/4-2/5)\u00f77/10=",
    correct: "1/2",
    student: "1/4",
    steps: "3/4-2/5=7/20\n7/20\u00f77/10=7/20\u00d77/10=49/200=1/4",
  },
  {
    label: "分数除法 (单位量)",
    grade: 6,
    problem: "5/6\u00f7(3/4-1/6)=",
    correct: "10/7",
    student: "35/72",
    steps: "3/4-1/6=7/12\n5/6\u00f77/12=5/6\u00d77/12=35/72",
  },
  {
    label: "百分数综合",
    grade: 6,
    problem: "36\u00f7(3/5)\u00d725%=",
    correct: "15",
    student: "21.6",
    steps: "36\u00f73/5=21.6\n21.6\u00d725%=21.6",
  },
  {
    label: "比的应用",
    grade: 6,
    problem: "甲:乙=5:8，乙比甲多18，甲是多少？",
    correct: "30",
    student: "48",
    steps: "乙占8份，18\u00f75=3.6\n甲=5\u00d73.6=18",
  },
  {
    label: "圆的周长",
    grade: 6,
    problem: "圆形花坛半径4.5米，周长是多少米？(π取3.14)",
    correct: "28.26",
    student: "63.585",
    steps: "3.14\u00d74.5\u00d74.5=63.585",
  },
];

const cardReveal = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0 },
  transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] },
};

export default function DiagnosePage() {
  const [studentId, setStudentId] = useState(DEFAULT_STUDENT_ID);
  const [grade, setGrade] = useState(6);
  const [problem, setProblem] = useState("(3/4-2/5)\u00f77/10=");
  const [correctAnswer, setCorrectAnswer] = useState("1/2");
  const [studentAnswer, setStudentAnswer] = useState("1/4");
  const [studentSteps, setStudentSteps] = useState("3/4-2/5=7/20\n7/20\u00f77/10=7/20\u00d77/10=49/200=1/4");
  const [guidanceMode, setGuidanceMode] = useState<GuidanceMode>("standard");
  const [result, setResult] = useState<DifySessionDraftResponse | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [streamingRequest, setStreamingRequest] = useState<DifySessionDraftRequest | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);

  const handleStreamComplete = useCallback((res: DifySessionDraftResponse) => {
    setResult(res);
    setStreamingRequest(null);
  }, []);

  const handleStreamError = useCallback((error: string) => {
    setStreamError(error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResult(null);
    setValidationError(null);
    setStreamError(null);

    if (!problem.trim()) {
      setValidationError("请输入题目内容");
      return;
    }
    if (!studentAnswer.trim()) {
      setValidationError("请输入学生答案");
      return;
    }
    if (!correctAnswer.trim()) {
      setValidationError("请输入正确答案");
      return;
    }

    const body: DifySessionDraftRequest = {
      student_id: studentId,
      grade,
      problem_text: problem,
      correct_answer_text: correctAnswer,
      student_answer_text: studentAnswer,
      student_steps_text: studentSteps || null,
      guidance_mode: guidanceMode,
    };

    setStreamingRequest(body);
  }

  function fillExample(ex: DemoExample) {
    setGrade(ex.grade);
    setProblem(ex.problem);
    setCorrectAnswer(ex.correct);
    setStudentAnswer(ex.student);
    setStudentSteps(ex.steps ?? "");
    setResult(null);
    setStreamingRequest(null);
    setStreamError(null);
  }

  const loading = streamingRequest !== null && result === null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="mb-8"
      >
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-forest-100/80">
            <Stethoscope className="h-5 w-5 text-forest-600" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--tone-ink)] md:text-3xl">
            教师诊断演示
          </h1>
        </div>
        <p className="max-w-2xl pl-[52px] text-[13px] leading-relaxed text-muted-foreground">
          录入一条学生作答记录，查看 AI 错因诊断、练习草案和学生引导内容。
          所有结果均为<strong className="text-[var(--tone-accent-strong)]">待教师审核</strong>状态。
        </p>
        <div className="mt-4 flex items-center gap-3 pl-[52px]">
          <div className="h-px flex-1 bg-gradient-to-r from-forest-200 via-parchment-300 to-transparent" />
        </div>
      </motion.header>

      {/* Example pills */}
      <div className="mb-7 flex flex-wrap items-center gap-2.5 pl-[52px]">
        <span className="text-[12px] font-medium text-muted-foreground">快速填入</span>
        <span className="text-[12px] text-muted-foreground/50">|</span>
        {DEMO_EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            onClick={() => fillExample(ex)}
            className="inline-flex items-center rounded-full border border-forest-200/70 bg-forest-50/50 px-3.5 py-1.5 text-[13px] font-medium text-forest-700 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] hover:-translate-y-0.5 hover:border-forest-300 hover:bg-forest-100/60 hover:shadow-md hover:shadow-forest-200/20"
          >
            {ex.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Form */}
        <div className="surface-panel rounded-2xl">
          <div className="border-b border-[var(--tone-line)] px-6 py-5">
            <h2 className="flex items-center gap-2.5 text-base font-semibold text-[var(--tone-ink)]">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-forest-100/80">
                <ClipboardList className="h-3.5 w-3.5 text-forest-600" />
              </div>
              录入作答记录
            </h2>
            <p className="mt-1.5 pl-[38px] text-[12px] text-muted-foreground">
              填入题目和学生答案，快速获取诊断
            </p>
          </div>
          <div className="px-6 py-5">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="grade" className="text-[12px] font-medium text-muted-foreground">年级</Label>
                  <Input
                    id="grade"
                    type="number"
                    min={1}
                    max={6}
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                    className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="student" className="text-[12px] font-medium text-muted-foreground">学生</Label>
                  <Input
                    id="student"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="S001"
                    className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="mode" className="text-[12px] font-medium text-muted-foreground">引导模式</Label>
                  <Select
                    value={guidanceMode}
                    onValueChange={(val) =>
                      setGuidanceMode(val as GuidanceMode)
                    }
                  >
                    <SelectTrigger className="w-full rounded-xl border-[var(--tone-line)] bg-white/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">标准模式</SelectItem>
                      <SelectItem value="exploration">探索模式</SelectItem>
                      <SelectItem value="challenge">挑战模式</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

              <div className="space-y-1.5">
                <Label htmlFor="problem" className="text-[12px] font-medium text-muted-foreground">题目</Label>
                <Input
                  id="problem"
                  required
                  value={problem}
                  onChange={(e) => setProblem(e.target.value)}
                  placeholder="例：2/3\u00d73/4="
                  className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="correct" className="text-[12px] font-medium text-muted-foreground">正确答案</Label>
                  <Input
                    id="correct"
                    required
                    value={correctAnswer}
                    onChange={(e) => setCorrectAnswer(e.target.value)}
                    placeholder="1/2"
                    className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="student-ans" className="text-[12px] font-medium text-muted-foreground">学生答案</Label>
                  <Input
                    id="student-ans"
                    required
                    value={studentAnswer}
                    onChange={(e) => setStudentAnswer(e.target.value)}
                    placeholder="6/7"
                    className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="steps" className="text-[12px] font-medium text-muted-foreground">
                  解题步骤（可选，每行一步）
                </Label>
                <Textarea
                  id="steps"
                  value={studentSteps}
                  onChange={(e) => setStudentSteps(e.target.value)}
                  placeholder={"2/3\u00d73/4=\n= 2\u00d73 / 3\u00d74"}
                  className="rounded-xl border-[var(--tone-line)] bg-white/50 transition-colors focus:bg-white"
                />
              </div>

              <Button
                type="submit"
                className="w-full rounded-xl bg-forest-600 transition-all duration-300 hover:-translate-y-0.5 hover:bg-forest-700 hover:shadow-lg hover:shadow-forest-300/25"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    诊断中...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    开始诊断
                  </>
                )}
              </Button>

              {validationError && (
                <p className="text-[13px] text-volcano-500">{validationError}</p>
              )}
            </form>
          </div>
        </div>

        {/* Right: Results */}
        <div className="space-y-4">
          {streamingRequest && !result && (
            <PipelineProgress
              request={streamingRequest}
              onComplete={handleStreamComplete}
              onError={handleStreamError}
            />
          )}

          <AnimatePresence mode="wait">
            {result && (
              <motion.div
                key="result"
                {...cardReveal}
                className="space-y-4"
              >
                {/* Review status */}
                <div className="flex items-center gap-2.5">
                  <Badge
                    variant="outline"
                    className="border-warm-300 bg-warm-50/60 px-2.5 py-0.5 text-[11px] font-medium text-warm-500"
                  >
                    待教师审核
                  </Badge>
                  <span className="text-[11px] text-muted-foreground">
                    AI 输出仅供参考，请审核后再用于课堂
                  </span>
                </div>

                {/* Diagnosis Result */}
                <div className="surface-panel rounded-2xl">
                  <div className="border-b border-[var(--tone-line)] px-5 py-4">
                    <h3 className="flex items-center gap-2.5 text-[15px] font-semibold text-[var(--tone-ink)]">
                      {result.diagnosis.is_correct ? (
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-forest-100">
                          <CheckCircle2 className="h-3.5 w-3.5 text-forest-600" />
                        </div>
                      ) : (
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-volcano-50">
                          <AlertTriangle className="h-3.5 w-3.5 text-volcano-500" />
                        </div>
                      )}
                      诊断结果
                    </h3>
                  </div>
                  <div className="space-y-3.5 px-5 py-4">
                    {result.diagnosis.is_correct ? (
                      <div>
                        <Badge className="bg-forest-600 hover:bg-forest-700">答案正确</Badge>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center gap-2.5">
                          <Badge className="bg-volcano-500 hover:bg-volcano-500/90 px-2.5 py-0.5 text-[12px]">
                            {result.diagnosis.primary_error.code}
                          </Badge>
                          <span className="text-[14px] font-medium text-[var(--tone-ink)]">
                            {result.diagnosis.primary_error.label}
                          </span>
                          <span className="text-[11px] text-muted-foreground">
                            置信度 {(result.diagnosis.primary_error.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <div className="rounded-xl bg-muted/40 p-3.5">
                          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                            证据
                          </p>
                          <p className="text-[13px] leading-relaxed text-[var(--tone-ink)]">
                            {result.diagnosis.primary_error.evidence}
                          </p>
                        </div>

                        <div className="rounded-xl bg-primary/5 p-3.5">
                          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-primary">
                            建议教师动作
                          </p>
                          <p className="text-[13px] leading-relaxed text-[var(--tone-ink)]">
                            {result.diagnosis.primary_error.teacher_action}
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {!result.diagnosis.is_correct && (
                  <VerticalCalcAnimation
                    expression={problem.replace(/=$/, "")}
                    correctAnswer={correctAnswer}
                    studentAnswer={studentAnswer}
                    errorType={result.diagnosis.primary_error.code}
                    autoPlay={false}
                  />
                )}

                {/* Teacher Summary */}
                <div className="surface-soft rounded-2xl">
                  <div className="border-b border-[var(--tone-line)] px-5 py-4">
                    <h3 className="flex items-center gap-2.5 text-[14px] font-semibold text-[var(--tone-ink)]">
                      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/10">
                        <BookOpen className="h-3.5 w-3.5 text-primary" />
                      </div>
                      教师摘要
                    </h3>
                  </div>
                  <div className="px-5 py-4">
                    <MarkdownContent content={result.teacher_summary} />
                  </div>
                </div>

                {/* Practice Recommendation */}
                {result.practice.items.length > 0 && (
                  <div className="surface-soft rounded-2xl">
                    <div className="border-b border-[var(--tone-line)] px-5 py-4">
                      <h3 className="flex items-center gap-2.5 text-[14px] font-semibold text-[var(--tone-ink)]">
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-warm-50">
                          <Lightbulb className="h-3.5 w-3.5 text-warm-500" />
                        </div>
                        练习草案（预计 {result.practice.estimated_minutes} 分钟）
                      </h3>
                    </div>
                    <div className="px-5 py-4">
                      <ul className="space-y-3">
                        {result.practice.items.map((item, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-3"
                          >
                            <Badge
                              variant="outline"
                              className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-forest-200 p-0 text-[10px] font-semibold text-forest-600"
                            >
                              {i + 1}
                            </Badge>
                            <div className="text-[13px] leading-relaxed">
                              <span className="font-medium text-[var(--tone-ink)]">
                                {item.problem}
                              </span>
                              <span className="ml-2 text-muted-foreground">
                                {item.reason}
                              </span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Student Feedback Preview */}
                <div className="rounded-2xl border border-sage-200/70 bg-sage-50/30">
                  <div className="border-b border-sage-200/50 px-5 py-4">
                    <h3 className="flex items-center gap-2.5 text-[14px] font-semibold text-[var(--tone-ink)]">
                      <span className="text-[15px]">🌱</span>
                      学生引导预览
                    </h3>
                    <p className="mt-1 pl-[27px] text-[11px] text-muted-foreground">
                      审核通过后，学生将看到以下引导内容
                    </p>
                  </div>
                  <div className="space-y-3.5 px-5 py-4">
                    <div className="rounded-xl bg-white/60 p-3.5">
                      <MarkdownContent content={result.student_feedback.message} />
                    </div>
                    {result.student_feedback.guiding_questions.length > 0 && (
                      <div className="space-y-2.5">
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                          引导提问
                        </p>
                        {result.student_feedback.guiding_questions.map((q, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2.5 text-[13px]"
                          >
                            <span className="shrink-0 font-semibold text-primary">Q{i + 1}</span>
                            <span className="text-[var(--tone-ink)]">{q}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <Separator className="bg-sage-200/50" />
                    <div className="flex items-start gap-2.5 text-[13px]">
                      <span className="shrink-0 text-[11px] font-medium text-muted-foreground">
                        下一步
                      </span>
                      <MarkdownContent content={result.student_feedback.next_step} className="[&_p]:text-[var(--tone-ink)]" />
                    </div>
                  </div>
                </div>

                {/* Encouragement */}
                {result.encouragement_message && (
                  <div className="flex items-center gap-2.5 rounded-xl bg-warm-50/50 border border-warm-200/40 px-4 py-3 text-[13px] text-bark-600">
                    <span className="text-[15px]">🌞</span>
                    {result.encouragement_message}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {streamError && !result && (
            <div className="flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50/50 px-4 py-3 text-[13px] text-red-600">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {streamError}
            </div>
          )}

          {!result && !streamingRequest && !streamError && (
            <div className="flex h-72 items-center justify-center rounded-2xl border border-dashed border-[var(--tone-line)] bg-white/20">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/40">
                  <ClipboardList className="h-6 w-6 text-muted-foreground/40" />
                </div>
                <p className="text-[13px] text-muted-foreground">填入作答记录后点击&quot;开始诊断&quot;</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
