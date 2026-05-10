"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle } from "lucide-react";
import { useClassForest } from "@/lib/api/hooks";
import { DEFAULT_CLASS_ID } from "@/lib/config";
import type { QuizProblemItem } from "@/lib/types";

const ClassPrepView = dynamic(
  () => import("@/components/classroom/ClassPrepView").then((m) => ({ default: m.ClassPrepView })),
);
const WhiteboardDisplay = dynamic(
  () => import("@/components/classroom/WhiteboardDisplay").then((m) => ({ default: m.WhiteboardDisplay })),
  { ssr: false },
);
const QuizSummaryView = dynamic(
  () => import("@/components/classroom/QuizSummaryView").then((m) => ({ default: m.QuizSummaryView })),
);

type ViewState = "prep" | "whiteboard" | "summary";

const viewVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

export default function ClassroomPage() {
  const [view, setView] = useState<ViewState>("prep");
  const [quizId, setQuizId] = useState("");
  const [problems, setProblems] = useState<QuizProblemItem[]>([]);
  const [quizResponses, setQuizResponses] = useState<Array<{ sequence: number; response: string }>>([]);

  const { data: forest, isLoading, isError } = useClassForest(DEFAULT_CLASS_ID);

  const handleStartQuiz = useCallback((id: string, probs: QuizProblemItem[]) => {
    setQuizId(id);
    setProblems(probs);
    setQuizResponses([]);
    setView("whiteboard");
  }, []);

  const handleComplete = useCallback((responses: Array<{ sequence: number; response: string }>) => {
    setQuizResponses(responses);
    setView("summary");
  }, []);

  const handleBackToPrep = useCallback(() => {
    setView("prep");
    setProblems([]);
    setQuizResponses([]);
  }, []);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-xl bg-forest-100" />
      </div>
    );
  }

  if (isError || !forest) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50/50 p-10 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-red-700">无法加载班级数据</h2>
          <p className="text-sm text-red-600">
            请确认后端服务正在运行并已播种班级数据（G6C1）
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {view === "whiteboard" && problems.length > 0 && (
        <WhiteboardDisplay
          key={quizId}
          problems={problems}
          quizId={quizId}
          onExit={handleBackToPrep}
          onComplete={handleComplete}
        />
      )}

      <AnimatePresence mode="wait">
        {view === "prep" && (
          <motion.div key="prep" {...viewVariants} transition={{ duration: 0.3 }}>
            <ClassPrepView
              forest={forest}
              onStartQuiz={handleStartQuiz}
            />
          </motion.div>
        )}

        {view === "summary" && (
          <motion.div key="summary" {...viewVariants} transition={{ duration: 0.3 }}>
            <QuizSummaryView
              problems={problems}
              responses={quizResponses}
              onBack={handleBackToPrep}
              onNewQuiz={handleBackToPrep}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
