"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Maximize2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ERROR_LABELS, type ClassForestResponse, type EmotionState } from "@/lib/types";
import { generateQuiz, getQuiz } from "@/lib/api";
import type { QuizProblemItem } from "@/lib/types";

interface ClassPrepViewProps {
  forest: ClassForestResponse;
  onStartQuiz: (quizId: string, problems: QuizProblemItem[]) => void;
}

const ERROR_COLORS: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  E01: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-400" },
  E02: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-400" },
  E03: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", dot: "bg-red-400" },
  E04: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200", dot: "bg-purple-400" },
  E05: { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-200", dot: "bg-teal-400" },
  E06: { bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-200", dot: "bg-cyan-400" },
  E07: { bg: "bg-pink-50", text: "text-pink-700", border: "border-pink-200", dot: "bg-pink-400" },
  E08: { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-200", dot: "bg-indigo-400" },
  E09: { bg: "bg-lime-50", text: "text-lime-700", border: "border-lime-200", dot: "bg-lime-400" },
  E10: { bg: "bg-fuchsia-50", text: "text-fuchsia-700", border: "border-fuchsia-200", dot: "bg-fuchsia-400" },
  E11: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200", dot: "bg-orange-400" },
  E99: { bg: "bg-gray-50", text: "text-gray-700", border: "border-gray-200", dot: "bg-gray-400" },
};

const ERROR_DESCRIPTIONS: Record<string, string> = {
  E01: "口诀不熟，基础加减乘除算错",
  E02: "满十忘记进位，或进位加错",
  E03: "不够减忘记退位，连续退位出错",
  E04: "竖式数位没有对齐，导致错位",
  E05: "混合运算搞错了运算顺序",
  E06: "小数点或分数单位搞错了",
  E07: "抄题时数字或符号写错",
  E08: "漏算了部分积或中间步骤",
  E09: "对算理的理解不够充分",
  E10: "审题不清或单位理解错误",
  E11: "结果明显不合理但没验算",
};

const MOOD_CONFIG: Record<EmotionState, { emoji: string; label: string; color: string }> = {
  thriving: { emoji: "🌸", label: "蓬勃生长", color: "text-emerald-600 bg-emerald-50" },
  happy: { emoji: "🐦", label: "状态良好", color: "text-sky-600 bg-sky-50" },
  stable: { emoji: "🌿", label: "稳步前进", color: "text-primary bg-forest-50" },
  wilting: { emoji: "🍂", label: "稍有下滑", color: "text-amber-600 bg-amber-50" },
  struggling: { emoji: "🌧", label: "需要关注", color: "text-red-600 bg-red-50" },
};

export function ClassPrepView({ forest, onStartQuiz }: ClassPrepViewProps) {
  const [selectedErrors, setSelectedErrors] = useState<string[]>([
    ...new Set(["E05", "E06", "E10", "E09", ...forest.class_top_errors]),
  ].slice(0, 5));
  const [difficulty, setDifficulty] = useState<"A" | "B" | "C">("C");
  const [problemCount, setProblemCount] = useState(6);
  const [loading, setLoading] = useState(false);
  const [previewProblems, setPreviewProblems] = useState<QuizProblemItem[] | null>(null);
  const [generatedQuizId, setGeneratedQuizId] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const toggleError = (code: string) => {
    setSelectedErrors((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
    setPreviewProblems(null);
    setGenerateError(null);
  };

  const handleGenerate = async () => {
    if (selectedErrors.length === 0) return;
    setLoading(true);
    setGenerateError(null);
    try {
      const result = await generateQuiz({
        class_id: forest.class_id,
        grade: forest.grade,
        error_codes_target: selectedErrors,
        problem_count: problemCount,
        difficulty,
      });
      const quiz = await getQuiz(result.quiz_id);
      setPreviewProblems(quiz.problems);
      setGeneratedQuizId(result.quiz_id);
    } catch {
      setGenerateError("生成练习失败，请确认后端服务正在运行");
      setPreviewProblems(null);
    }
    setLoading(false);
  };

  const handleStart = async () => {
    if (!previewProblems) return;
    if (document.fullscreenEnabled && !document.fullscreenElement) {
      await document.documentElement.requestFullscreen().catch(() => {});
    }
    onStartQuiz(generatedQuizId ?? crypto.randomUUID(), previewProblems);
  };

  const allErrorCodes = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11"];
  const mood = MOOD_CONFIG[forest.class_emotional_state];
  const accPercent = Math.round(forest.class_accuracy * 100);
  const accColor = accPercent >= 80 ? "text-emerald-600" : accPercent >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--tone-ink)]">{forest.class_name} · 课堂模式</h1>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ring-black/5 ${mood.color}`}>
            {mood.emoji} {mood.label}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          基于班级共性问题生成随堂练习，投屏到大屏带做或小测
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: Class Error Portrait (3 cols) */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-3"
        >
          <Card className="surface-panel h-full rounded-[24px] border-0 shadow-none">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                班级错因画像
                <span className={`ml-auto text-2xl font-bold tabular-nums ${accColor}`}>{accPercent}%</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Accuracy bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>班级正确率</span>
                  <span>{forest.trees.length} 名学生</span>
                </div>
                <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${accPercent >= 80 ? "bg-emerald-500" : accPercent >= 60 ? "bg-amber-500" : "bg-red-500"}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${accPercent}%` }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                  />
                </div>
              </div>

              {/* Top errors with student distribution */}
              <div className="space-y-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">高频错因</p>
                {forest.class_top_errors.map((code, rank) => {
                  const c = ERROR_COLORS[code] || ERROR_COLORS.E99;
                  const count = forest.trees.filter((t) => t.dominant_errors.includes(code)).length;
                  const pct = forest.trees.length > 0 ? Math.round((count / forest.trees.length) * 100) : 0;
                  const desc = ERROR_DESCRIPTIONS[code] || "";
                  return (
                    <motion.div
                      key={code}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 + rank * 0.1 }}
                      className={`rounded-[18px] border ${c.border} ${c.bg} p-3`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className={`${c.bg} ${c.text} ${c.border} text-xs font-bold`}>
                          {code}
                        </Badge>
                        <span className="text-sm font-semibold text-foreground">
                          {ERROR_LABELS[code as keyof typeof ERROR_LABELS]}
                        </span>
                        <span className="ml-auto text-xs font-medium text-muted-foreground">
                          {count} 人 ({pct}%)
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-1.5">{desc}</p>
                      <div className="h-1.5 rounded-full bg-white/60 overflow-hidden">
                        <motion.div
                          className={`h-full rounded-full ${c.dot}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.6, delay: 0.4 + rank * 0.1 }}
                        />
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* Teaching tips */}
              <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-[var(--tone-soft)]/80 p-3 text-xs text-[var(--tone-ink)]/80">
                <span className="font-semibold">教学建议</span>
                <span className="ml-1">
                  {forest.class_top_errors.includes("E03") && "用数位表带学生复盘退位过程"}
                  {forest.class_top_errors.includes("E02") && " · 让学生在竖式中写出进位数字"}
                  {forest.class_top_errors.includes("E01") && " · 安排短时口诀闪卡练习"}
                  {forest.class_top_errors.includes("E05") && " · 让学生标注运算顺序"}
                  {!forest.class_top_errors.some((c) => ["E01", "E02", "E03", "E05"].includes(c)) && "关注高频错因，针对性出题练习"}
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right: Quiz Config (2 cols) */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="surface-panel h-full rounded-[24px] border-0 shadow-none">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">随堂测验配置</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Error code selection */}
              <div>
                <label className="mb-2 block text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  目标错因
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {allErrorCodes.map((code) => {
                    const c = ERROR_COLORS[code];
                    const selected = selectedErrors.includes(code);
                    const isTop = forest.class_top_errors.includes(code);
                    return (
                      <button
                        key={code}
                        onClick={() => toggleError(code)}
                        className={`relative flex items-center gap-1.5 rounded-lg border px-2.5 py-2 text-left text-xs transition-all ${
                          selected
                            ? `${c.bg} ${c.border} ${c.text} font-medium shadow-sm`
                            : "border-border bg-card text-muted-foreground hover:border-primary/30 hover:bg-muted/50"
                        }`}
                      >
                        <span className="font-bold">{code}</span>
                        <span className="truncate">{ERROR_LABELS[code as keyof typeof ERROR_LABELS]}</span>
                        {isTop && !selected && (
                          <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-[var(--tone-accent)]" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Difficulty + Count */}
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="mb-1.5 block text-xs font-semibold text-muted-foreground">难度</label>
                  <div className="flex gap-1">
                    {(["A", "B", "C"] as const).map((d) => (
                      <button
                        key={d}
                        onClick={() => { setDifficulty(d); setPreviewProblems(null); }}
                        className={`flex-1 rounded-lg border px-2 py-2 text-xs transition-all ${
                          difficulty === d
                            ? "border-primary bg-primary/10 font-semibold text-primary shadow-sm"
                            : "border-border text-muted-foreground hover:border-primary/30"
                        }`}
                      >
                        {d === "A" ? "🌱 基础" : d === "B" ? "🌿 中等" : "🌳 挑战"}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-muted-foreground">题数</label>
                  <select
                    value={problemCount}
                    onChange={(e) => { setProblemCount(Number(e.target.value)); setPreviewProblems(null); }}
                    className="w-full rounded-xl border border-[color:var(--tone-line)] bg-white/90 px-3 py-2 text-xs text-[var(--tone-ink)]"
                  >
                    {[3, 4, 5, 6, 7, 8].map((n) => (
                      <option key={n} value={n}>{n} 题</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Generate button */}
              <Button
                onClick={handleGenerate}
                disabled={selectedErrors.length === 0 || loading}
                className="relative w-full overflow-hidden rounded-full bg-[var(--tone-accent-strong)] text-white hover:bg-[color:color-mix(in_oklab,var(--tone-accent-strong)_88%,black)]"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="inline-block"
                    >
                      ✦
                    </motion.span>
                    生成中...
                  </span>
                ) : previewProblems ? "🔄 重新生成" : "✨ 生成随堂练习"}
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {generateError && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {generateError}
        </div>
      )}

      {/* Preview */}
      <AnimatePresence>
        {previewProblems && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="surface-panel rounded-[24px] border-0 shadow-none">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    预览
                    <span className="text-sm font-normal text-muted-foreground">({previewProblems.length} 题)</span>
                  </CardTitle>
                  <Button onClick={handleStart} size="lg" className="gap-2 rounded-full bg-[var(--tone-accent-strong)] text-white hover:bg-[color:color-mix(in_oklab,var(--tone-accent-strong)_88%,black)]">
                    <Maximize2 className="h-4 w-4" />
                    <span>打开教育屏全屏</span>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {previewProblems.map((p, i) => {
                    const c = ERROR_COLORS[p.target_error_code || ""] || ERROR_COLORS.E99;
                    return (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.05 }}
                        className={`flex items-center gap-2 rounded-[18px] border ${c.border} ${c.bg} px-3 py-2.5`}
                      >
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/60 text-[10px] font-bold text-muted-foreground">
                          {p.sequence}
                        </span>
                        <span className="font-semibold text-foreground text-sm">{p.problem}</span>
                        <span className="ml-auto text-xs text-muted-foreground">= {p.correct_answer}</span>
                      </motion.div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
