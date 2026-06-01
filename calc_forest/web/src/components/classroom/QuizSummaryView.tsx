"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { QuizProblemItem } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";

interface QuizSummaryViewProps {
  problems: QuizProblemItem[];
  responses: Array<{ sequence: number; response: string }>;
  onBack: () => void;
  onNewQuiz: () => void;
}

const RESPONSE_STYLES: Record<string, { label: string; icon: string; color: string; bg: string; ring: string }> = {
  mostly_correct: { label: "多数对了", icon: "👏", color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200", ring: "border-l-emerald-400" },
  mixed: { label: "一半一半", icon: "🤔", color: "text-amber-700", bg: "bg-amber-50 border-amber-200", ring: "border-l-amber-400" },
  mostly_wrong: { label: "需要再练", icon: "💪", color: "text-orange-700", bg: "bg-orange-50 border-orange-200", ring: "border-l-orange-400" },
};

export function QuizSummaryView({ problems, responses, onBack, onNewQuiz }: QuizSummaryViewProps) {
  const stats = useMemo(() => {
    const correct = responses.filter((r) => r.response === "mostly_correct").length;
    const mixed = responses.filter((r) => r.response === "mixed").length;
    const wrong = responses.filter((r) => r.response === "mostly_wrong").length;
    const errorCodes = responses
      .filter((r) => r.response !== "mostly_correct")
      .map((r) => {
        const p = problems.find((pp) => pp.sequence === r.sequence);
        return p?.target_error_code;
      })
      .filter(Boolean) as string[];

    const errorDist: Record<string, number> = {};
    errorCodes.forEach((code) => {
      errorDist[code] = (errorDist[code] || 0) + 1;
    });

    const ratio = correct / Math.max(responses.length, 1);
    const mood = ratio >= 0.7 ? "great" : ratio >= 0.4 ? "okay" : "tough";
    const moodConfig = {
      great: { emoji: "🌳", title: "课堂表现优秀！", message: "大部分知识点已经掌握，继续保持！", color: "text-emerald-600", barColor: "bg-emerald-500" },
      okay: { emoji: "🌿", title: "稳步进步中", message: "部分知识点还需要巩固，课后可以针对性练习。", color: "text-amber-600", barColor: "bg-amber-500" },
      tough: { emoji: "🌱", title: "找到薄弱点了", message: "这正是练习的意义所在！课后重点攻克这些错因。", color: "text-orange-600", barColor: "bg-orange-500" },
    };

    return { correct, mixed, wrong, errorDist, total: responses.length, mood, moodConfig: moodConfig[mood], ratio };
  }, [problems, responses]);

  const topErrors = Object.entries(stats.errorDist)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  const isGreat = stats.mood === "great";

  return (
    <div className="relative space-y-6">
      {/* Celebration sparkles */}
      {isGreat && (
        <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden">
          {Array.from({ length: 16 }, (_, i) => (
            <motion.div
              key={i}
              className="absolute text-xl"
              style={{
                left: `${10 + (i * 6) % 80}%`,
                top: `${5 + (i * 9) % 60}%`,
              }}
              initial={{ opacity: 0, scale: 0, y: 20 }}
              animate={{ opacity: [0, 1, 1, 0], scale: [0, 1.2, 1, 0.8], y: [-20, -40] }}
              transition={{ duration: 2, delay: i * 0.15, repeat: Infinity, repeatDelay: 3 }}
            >
              {["🌸", "✨", "🌿", "⭐"][i % 4]}
            </motion.div>
          ))}
        </div>
      )}

      {/* Header with mood */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <motion.div
          className="text-5xl mb-2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", damping: 10, stiffness: 200, delay: 0.2 }}
        >
          {stats.moodConfig.emoji}
        </motion.div>
        <h1 className={`text-xl font-bold ${stats.moodConfig.color}`}>{stats.moodConfig.title}</h1>
        <p className="text-sm text-muted-foreground">{stats.moodConfig.message}</p>
      </motion.div>

      {/* Stat cards */}
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 }}>
        <Card className="surface-panel rounded-[24px] border-0 shadow-none">
          <CardContent className="py-6">
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: stats.correct, label: "多数对了", color: "text-emerald-600", bg: "bg-emerald-50", icon: "👏" },
                { value: stats.mixed, label: "一半一半", color: "text-amber-600", bg: "bg-amber-50", icon: "🤔" },
                { value: stats.wrong, label: "需要再练", color: "text-orange-600", bg: "bg-orange-50", icon: "💪" },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 + i * 0.1 }}
                  className={`rounded-xl ${item.bg} p-4 text-center`}
                >
                  <div className="text-2xl mb-1">{item.icon}</div>
                  <div className={`text-3xl font-bold tabular-nums ${item.color}`}>{item.value}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{item.label}</div>
                </motion.div>
              ))}
            </div>

            {/* Overall bar */}
            <div className="mt-5 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">课堂掌握率</span>
                <span className={`font-bold ${stats.moodConfig.color}`}>{Math.round(stats.ratio * 100)}%</span>
              </div>
              <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${stats.moodConfig.barColor}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${stats.ratio * 100}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid gap-4 md:grid-cols-5">
        {/* Per-problem list */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }} className="md:col-span-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">逐题反馈</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5">
              {problems.map((p, i) => {
                const resp = responses.find((r) => r.sequence === p.sequence);
                const style = resp ? RESPONSE_STYLES[resp.response] : null;
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.35 + i * 0.05 }}
                    className={`flex items-center gap-2.5 rounded-lg border ${style ? `${style.bg} ${style.ring} border-l-[3px]` : "bg-muted/30 border-transparent"} px-3 py-2`}
                  >
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/70 text-[10px] font-bold text-muted-foreground">
                      {p.sequence}
                    </span>
                    <span className="font-medium text-sm">{p.problem}</span>
                    <span className="text-xs text-muted-foreground">= {p.correct_answer}</span>
                    {style && (
                      <span className={`ml-auto text-xs font-medium ${style.color} flex items-center gap-1`}>
                        {style.icon} {style.label}
                      </span>
                    )}
                  </motion.div>
                );
              })}
            </CardContent>
          </Card>
        </motion.div>

        {/* Error distribution */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }} className="md:col-span-2">
          <Card className="surface-panel h-full rounded-[24px] border-0 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">错因分布</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topErrors.length > 0 ? topErrors.map(([code, count], i) => (
                <motion.div
                  key={code}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  className="space-y-1.5"
                >
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold">
                      {code} {ERROR_LABELS[code as keyof typeof ERROR_LABELS]}
                    </span>
                    <span className="text-muted-foreground text-xs">{count} 题</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-[var(--tone-accent)]"
                      initial={{ width: 0 }}
                      animate={{ width: `${(count / stats.total) * 100}%` }}
                      transition={{ duration: 0.6, delay: 0.6 + i * 0.1 }}
                    />
                  </div>
                </motion.div>
              )) : (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-4 text-center text-sm text-emerald-600 font-medium"
                >
                  🎉 全部掌握！可以进入下一知识点。
                </motion.p>
              )}

              {/* Recommendation */}
              {topErrors.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="rounded-xl border border-primary/20 bg-primary/5 p-3 mt-4"
                >
                  <p className="text-sm font-semibold text-primary">下一步建议</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    可针对 {topErrors.map(([c]) => c).join("、")} 类型生成个性化课后作业，让学生巩固练习。
                  </p>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Actions */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="flex flex-wrap justify-center gap-3">
        <Button variant="outline" onClick={onBack} className="rounded-full border-[color:var(--tone-line)] bg-white/80 text-[var(--tone-ink)] hover:bg-white">← 返回准备</Button>
        <Button onClick={onNewQuiz} className="gap-1 rounded-full bg-[var(--tone-accent-strong)] text-white hover:bg-[color:color-mix(in_oklab,var(--tone-accent-strong)_88%,black)]">🔄 再来一组</Button>
      </motion.div>
    </div>
  );
}
