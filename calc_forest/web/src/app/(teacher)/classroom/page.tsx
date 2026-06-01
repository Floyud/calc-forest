"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, LayoutPanelTop, MonitorPlay, NotebookPen } from "lucide-react";
import { useClassForest } from "@/lib/api/hooks";
import { DEFAULT_CLASS_ID } from "@/lib/config";
import type { QuizProblemItem } from "@/lib/types";
import {
  InsightStrip,
  PageHero,
  SectionPanel,
  WorkspacePage,
} from "@/components/layout/workspace-shell";

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
  const [confirmExit, setConfirmExit] = useState(false);
  const viewRef = useRef(view);

  useEffect(() => { viewRef.current = view; }, [view]);

  const { data: forest, isLoading, isError } = useClassForest(DEFAULT_CLASS_ID);

  useEffect(() => {
    if (view !== "whiteboard") return;
    window.history.pushState({ view: "whiteboard" }, "");

    const handlePopState = () => {
      if (viewRef.current === "whiteboard") {
        window.history.pushState({ view: "whiteboard" }, "");
        setConfirmExit(true);
      }
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [view]);

  const handleStartQuiz = useCallback((id: string, probs: QuizProblemItem[]) => {
    setQuizId(id);
    setProblems(probs);
    setQuizResponses([]);
    setConfirmExit(false);
    setView("whiteboard");
  }, []);

  const handleComplete = useCallback((responses: Array<{ sequence: number; response: string }>) => {
    setQuizResponses(responses);
    setConfirmExit(false);
    setView("summary");
  }, []);

  const handleBackToPrep = useCallback(() => {
    setView("prep");
    setProblems([]);
    setQuizResponses([]);
    setConfirmExit(false);
  }, []);

  const handleConfirmExitCancel = useCallback(() => {
    setConfirmExit(false);
  }, []);

  const handleConfirmExitConfirm = useCallback(() => {
    setView("prep");
    setProblems([]);
    setQuizResponses([]);
    setConfirmExit(false);
  }, []);

  if (isLoading) {
    return (
      <WorkspacePage>
        <div className="surface-hero h-56 animate-pulse rounded-[28px]" />
        <div className="surface-panel h-80 animate-pulse rounded-[24px]" />
      </WorkspacePage>
    );
  }

  if (isError || !forest) {
    return (
      <WorkspacePage>
        <div className="flex flex-col items-center justify-center gap-4 rounded-[24px] border border-red-200 bg-red-50/50 p-10 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-red-700">无法加载班级数据</h2>
          <p className="text-sm text-red-600">
            请确认后端服务正在运行并已播种班级数据（G6C1）
          </p>
        </div>
      </WorkspacePage>
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

      {confirmExit && view === "whiteboard" && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="mx-4 max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-foreground">确认退出？</h3>
            <p className="mt-2 text-sm text-muted-foreground">课堂答题正在进行中，退出后将丢失当前进度。</p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={handleConfirmExitCancel}
                className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:bg-gray-100"
              >
                继续答题
              </button>
              <button
                onClick={handleConfirmExitConfirm}
                className="rounded-lg bg-red-500 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"
              >
                退出
              </button>
            </div>
          </div>
        </div>
      )}

      <AnimatePresence mode="wait">
        {view === "prep" && (
          <motion.div key="prep" {...viewVariants} transition={{ duration: 0.3 }}>
            <WorkspacePage>
              <PageHero
                eyebrow="课堂模式"
                title="先看班级共性错因，再决定这一节课要怎么讲。"
                description="课堂模式把备课、投屏和课后总结拆成三种明确状态。老师先从班级画像出发，再进入大屏讲评，最后回看课堂结果。"
                metric={{
                  label: "当前阶段",
                  value: "课前备课",
                  note: `${forest.class_name} · 共 ${forest.trees.length} 名学生`,
                }}
                aside={(
                  <div className="space-y-3">
                    <InsightStrip
                      title="阶段一"
                      value="课前备课"
                      detail="查看共性错因、选择目标错误类型和题目难度。"
                    />
                    <InsightStrip
                      title="阶段二"
                      value="投屏讲评"
                      detail="进入大屏白板态，只保留题目、提示和响应控制。"
                    />
                    <InsightStrip
                      title="阶段三"
                      value="课后总结"
                      detail="汇总课堂掌握率与下一步教学建议。"
                    />
                  </div>
                )}
              />
              <SectionPanel
                title="课前备课台"
                description="围绕班级高频错因生成一组可直接投屏的随堂练习。"
              >
                <ClassPrepView
                  forest={forest}
                  onStartQuiz={handleStartQuiz}
                />
              </SectionPanel>
            </WorkspacePage>
          </motion.div>
        )}

        {view === "summary" && (
          <motion.div key="summary" {...viewVariants} transition={{ duration: 0.3 }}>
            <WorkspacePage>
              <PageHero
                eyebrow="课堂总结"
                title="这一轮讲评结束后，老师需要看到什么。"
                description="总结页不做庆祝海报，而是回到教学判断：哪些题已经掌握，哪些错因还需要延续到课后作业或个别跟进。"
                metric={{
                  label: "当前阶段",
                  value: "课后总结",
                  note: `本次课堂共 ${problems.length} 题`,
                }}
                aside={(
                  <div className="space-y-3">
                    <InsightStrip
                      title="回流路径"
                      value="课堂讲评 → 作业巩固"
                      detail="若仍有薄弱点，可继续引导至作业批阅或单题诊断。"
                    />
                    <InsightStrip
                      title="讲评视角"
                      value="关注共性，不放大学生压力"
                      detail="仍然遵守低压力表达和教师主导的原则。"
                    />
                  </div>
                )}
              />
              <SectionPanel
                title="课后总结台"
                description="查看课堂掌握率、逐题反馈和下一步教学建议。"
                action={(
                  <div className="hidden items-center gap-2 md:flex">
                    <div className="rounded-full bg-[var(--tone-soft)] px-3 py-1.5 text-xs text-[var(--tone-muted)]">
                      <NotebookPen className="mr-1 inline h-3.5 w-3.5" />
                      可继续回到备课台再出一组题
                    </div>
                  </div>
                )}
              >
                <QuizSummaryView
                  problems={problems}
                  responses={quizResponses}
                  onBack={handleBackToPrep}
                  onNewQuiz={handleBackToPrep}
                />
              </SectionPanel>
            </WorkspacePage>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
