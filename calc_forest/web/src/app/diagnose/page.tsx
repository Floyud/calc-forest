"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  ClipboardList,
  Lightbulb,
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
import type { DifySessionDraftResponse, GuidanceMode } from "@/lib/types";
import { useSessionDraft } from "@/lib/api/hooks";

type DemoExample = {
  label: string;
  grade: number;
  problem: string;
  correct: string;
  student: string;
};

const DEMO_EXAMPLES: DemoExample[] = [
  {
    label: "分数乘法 (2/3 × 3/4)",
    grade: 6,
    problem: "2/3×3/4=",
    correct: "1/2",
    student: "6/7",
  },
  {
    label: "分数除法 (5/6 ÷ 2/3)",
    grade: 6,
    problem: "5/6÷2/3=",
    correct: "5/4",
    student: "5/9",
  },
  {
    label: "百分数计算 (240×35%)",
    grade: 6,
    problem: "240×35%=",
    correct: "84",
    student: "840",
  },
  {
    label: "化简比 (0.75:1.25)",
    grade: 6,
    problem: "化简比 0.75:1.25",
    correct: "3:5",
    student: "75:125",
  },
];

export default function DiagnosePage() {
  const [grade, setGrade] = useState(6);
  const [problem, setProblem] = useState("2/3×3/4=");
  const [correctAnswer, setCorrectAnswer] = useState("1/2");
  const [studentAnswer, setStudentAnswer] = useState("6/7");
  const [studentSteps, setStudentSteps] = useState("");
  const [guidanceMode, setGuidanceMode] = useState<GuidanceMode>("standard");
  const [result, setResult] = useState<DifySessionDraftResponse | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const sessionDraft = useSessionDraft();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResult(null);
    setValidationError(null);

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

    const body = {
      grade,
      problem_text: problem,
      correct_answer_text: correctAnswer,
      student_answer_text: studentAnswer,
      student_steps_text: studentSteps || null,
      guidance_mode: guidanceMode,
    };

    try {
      const res = await sessionDraft.mutateAsync(body);
      setResult(res);
    } catch {
      setResult(null);
    }
  }

  function fillExample(ex: DemoExample) {
    setGrade(ex.grade);
    setProblem(ex.problem);
    setCorrectAnswer(ex.correct);
    setStudentAnswer(ex.student);
    setStudentSteps("");
    setResult(null);
  }

  const loading = sessionDraft.isPending;
  const apiError = sessionDraft.isError;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-8">
        <h1 className="mb-2 text-2xl font-bold md:text-3xl">
          教师诊断演示
        </h1>
        <p className="text-muted-foreground">
          录入一条学生作答记录，查看 AI 错因诊断、练习草案和学生引导内容。
          所有结果均为<strong>待教师审核</strong>状态。
        </p>
      </div>

      {/* Example buttons */}
      <div className="mb-6 flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground">快速填入示例：</span>
        {DEMO_EXAMPLES.map((ex) => (
          <Button
            key={ex.label}
            variant="outline"
            size="sm"
            onClick={() => fillExample(ex)}
          >
            {ex.label}
          </Button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ClipboardList className="h-5 w-5 text-primary" />
              录入作答记录
            </CardTitle>
            <CardDescription>
              填入题目和学生答案，快速获取诊断
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="grade">年级</Label>
                  <Input
                    id="grade"
                    type="number"
                    min={1}
                    max={6}
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="mode">引导模式</Label>
                  <Select
                    value={guidanceMode}
                    onValueChange={(val) =>
                      setGuidanceMode(val as GuidanceMode)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">标准模式</SelectItem>
                      <SelectItem value="exploration">探索模式</SelectItem>
                      <SelectItem value="challenge">挑战模式</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="problem">题目</Label>
                <Input
                  id="problem"
                  required
                  value={problem}
                  onChange={(e) => setProblem(e.target.value)}
                  placeholder="例：2/3×3/4="
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="correct">正确答案</Label>
                  <Input
                    id="correct"
                    required
                    value={correctAnswer}
                    onChange={(e) => setCorrectAnswer(e.target.value)}
                    placeholder="1/2"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="student">学生答案</Label>
                  <Input
                    id="student"
                    required
                    value={studentAnswer}
                    onChange={(e) => setStudentAnswer(e.target.value)}
                    placeholder="6/7"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="steps">
                  解题步骤（可选，每行一步）
                </Label>
                <Textarea
                  id="steps"
                  value={studentSteps}
                  onChange={(e) => setStudentSteps(e.target.value)}
                  placeholder={"2/3×3/4=\n= 2×3 / 3×4"}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
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
                <p className="text-sm text-rose-500">{validationError}</p>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Right: Result */}
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {/* Review status */}
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-fruit-400 text-fruit-500">
                    待教师审核
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    AI 输出仅供参考，请审核后再用于课堂
                  </span>
                </div>

                {/* Diagnosis Result */}
                <Card className="border-forest-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      {result.diagnosis.is_correct ? (
                        <CheckCircle2 className="h-5 w-5 text-forest-600" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-fruit-500" />
                      )}
                      诊断结果
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {result.diagnosis.is_correct ? (
                      <div>
                        <Badge className="bg-forest-600">答案正确</Badge>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-fruit-500">
                            {result.diagnosis.primary_error.code}
                          </Badge>
                          <span className="font-medium">
                            {result.diagnosis.primary_error.label}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            置信度{" "}
                            {(result.diagnosis.primary_error.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <div className="rounded-md bg-muted/50 p-3">
                          <p className="mb-1 text-xs font-medium text-muted-foreground">
                            证据
                          </p>
                          <p className="text-sm leading-relaxed">
                            {result.diagnosis.primary_error.evidence}
                          </p>
                        </div>

                        <div className="rounded-md bg-primary/5 p-3">
                          <p className="mb-1 text-xs font-medium text-primary">
                            建议教师动作
                          </p>
                          <p className="text-sm leading-relaxed">
                            {result.diagnosis.primary_error.teacher_action}
                          </p>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Teacher Summary */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <BookOpen className="h-4 w-4 text-primary" />
                      教师摘要
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-relaxed">
                      {result.teacher_summary}
                    </p>
                  </CardContent>
                </Card>

                {/* Practice Recommendation */}
                {result.practice.items.length > 0 && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Lightbulb className="h-4 w-4 text-warm-500" />
                        练习草案（预计 {result.practice.estimated_minutes} 分钟）
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {result.practice.items.map((item, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-2 text-sm"
                          >
                            <Badge
                              variant="outline"
                              className="mt-0.5 shrink-0 text-xs"
                            >
                              {i + 1}
                            </Badge>
                            <div>
                              <span className="font-medium">
                                {item.problem}
                              </span>
                              <span className="ml-2 text-muted-foreground">
                                {item.reason}
                              </span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Student Feedback Preview */}
                <Card className="border-sky-200 bg-sky-50/30">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <span className="text-base">🌱</span>
                      学生引导预览
                    </CardTitle>
                    <CardDescription>
                      审核通过后，学生将看到以下引导内容
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="rounded-md bg-white p-3">
                      <p className="text-sm leading-relaxed">
                        {result.student_feedback.message}
                      </p>
                    </div>
                    {result.student_feedback.guiding_questions.length > 0 && (
                      <div className="space-y-1.5">
                        <p className="text-xs font-medium text-muted-foreground">
                          引导提问
                        </p>
                        {result.student_feedback.guiding_questions.map((q, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 text-sm"
                          >
                            <span className="text-primary">Q{i + 1}</span>
                            <span>{q}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <Separator />
                    <div className="flex items-start gap-2 text-sm">
                      <span className="shrink-0 text-xs text-muted-foreground">
                        下一步
                      </span>
                      <span>{result.student_feedback.next_step}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Encouragement */}
                {result.encouragement_message && (
                  <div className="flex items-center gap-2 rounded-xl bg-warm-100/60 p-3 text-sm text-bark-600">
                    <span className="text-lg">🌞</span>
                    {result.encouragement_message}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {apiError && !result && (
            <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              诊断请求失败，请确认后端服务正在运行
            </div>
          )}

          {!result && !apiError && (
            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
              <div className="text-center">
                <ClipboardList className="mx-auto mb-2 h-8 w-8 opacity-40" />
                <p className="text-sm">填入作答记录后点击&quot;开始诊断&quot;</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
