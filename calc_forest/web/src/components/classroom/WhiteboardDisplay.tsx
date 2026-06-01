"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { QuizProblemItem, WhiteboardStep, ClassResponse } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";
import { recordQuizResponse } from "@/lib/api";

interface WhiteboardDisplayProps {
  problems: QuizProblemItem[];
  quizId: string;
  onExit: () => void;
  onComplete: (responses: Array<{ sequence: number; response: string }>) => void;
}

const RESPONSE_CONFIG: Record<ClassResponse, { label: string; icon: string; color: string; ring: string }> = {
  mostly_correct: {
    label: "多数对了",
    icon: "👏",
    color: "bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-white shadow-lg shadow-emerald-500/30",
    ring: "ring-emerald-300",
  },
  mixed: {
    label: "一半一半",
    icon: "🤔",
    color: "bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-white shadow-lg shadow-amber-500/30",
    ring: "ring-amber-300",
  },
  mostly_wrong: {
    label: "需要再练",
    icon: "💪",
    color: "bg-orange-500 hover:bg-orange-400 active:bg-orange-600 text-white shadow-lg shadow-orange-500/30",
    ring: "ring-orange-300",
  },
};

const skyStyles: Record<string, { bg: string; ground: string[] }> = {
  default: {
    bg: "bg-gradient-to-br from-[#163f31] via-[#0f241c] to-[#08120f]",
    ground: ["#215846", "#163f31", "#102a20"],
  },
  correct: {
    bg: "bg-gradient-to-br from-[#17644d] via-[#0f3126] to-[#08120f]",
    ground: ["#2b7a61", "#1f5d49", "#164535"],
  },
  wrong: {
    bg: "bg-gradient-to-br from-[#4a3418] via-[#1f2719] to-[#08120f]",
    ground: ["#8a6633", "#5f4b2c", "#44351f"],
  },
};

export function WhiteboardDisplay({ problems, quizId, onExit, onComplete }: WhiteboardDisplayProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [step, setStep] = useState<WhiteboardStep>("showing_problem");
  const [responses, setResponses] = useState<Record<number, ClassResponse>>({});
  const [skyKey, setSkyKey] = useState("default");
  const [showControls, setShowControls] = useState(true);
  const [confirmExit, setConfirmExit] = useState(false);
  const [cardKey, setCardKey] = useState(0);
  const [syncError, setSyncError] = useState<string | null>(null);

  const stepRef = useRef(step);
  const indexRef = useRef(currentIndex);
  const responsesRef = useRef(responses);
  const confirmExitRef = useRef(false);

  useEffect(() => { stepRef.current = step; }, [step]);
  useEffect(() => { indexRef.current = currentIndex; }, [currentIndex]);
  useEffect(() => { responsesRef.current = responses; }, [responses]);
  useEffect(() => { confirmExitRef.current = confirmExit; }, [confirmExit]);

  const problem = problems[currentIndex];
  const isLast = currentIndex === problems.length - 1;

  const sparklePositions = useMemo(() => Array.from({ length: 20 }, (_, i) => ({
    left: `${5 + (i * 5) % 90}%`,
    top: `${3 + (i * 7) % 45}%`,
    size: 4 + i % 4,
    delay: i * 0.25,
    duration: 1.8 + i % 3,
    color: i % 3 === 0 ? "#fde047" : i % 3 === 1 ? "#fbbf24" : "#fb923c",
  })), []);

  const idleTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetIdle = useCallback(() => {
    setShowControls(true);
    if (idleTimeout.current) clearTimeout(idleTimeout.current);
    idleTimeout.current = setTimeout(() => setShowControls(false), 4000);
  }, []);

  useEffect(() => {
    resetIdle();
    return () => { if (idleTimeout.current) clearTimeout(idleTimeout.current); };
  }, [resetIdle]);

  const transitionTo = useCallback((nextIndex: number, nextStep: WhiteboardStep, sky: string) => {
    setCardKey((k) => k + 1);
    setCurrentIndex(nextIndex);
    setStep(nextStep);
    setSkyKey(sky);
  }, []);

  const handleMarkResponse = useCallback(async (response: ClassResponse) => {
    const idx = indexRef.current;
    setResponses((prev) => ({ ...prev, [idx]: response }));
    setSkyKey(response === "mostly_correct" ? "correct" : response === "mostly_wrong" ? "wrong" : "default");
    setStep("showing_explanation");

    const p = problems[idx];
    try {
      await recordQuizResponse(quizId, {
        quiz_id: quizId,
        problem_sequence: p.sequence,
        class_response: response,
        notes: "",
      });
      setSyncError(null);
    } catch (err) {
      setSyncError("答题数据同步失败，请检查网络连接");
    }
  }, [problems, quizId]);

  const handleNext = useCallback(() => {
    const idx = indexRef.current;
    if (idx >= problems.length - 1) {
      const r = responsesRef.current;
      onComplete(
        Object.entries(r).map(([i, resp]) => ({
          sequence: problems[Number(i)].sequence,
          response: resp,
        })),
      );
      return;
    }
    transitionTo(idx + 1, "showing_problem", "default");
  }, [problems, onComplete, transitionTo]);

  const handlePrev = useCallback(() => {
    const idx = indexRef.current;
    if (idx > 0) transitionTo(idx - 1, "showing_problem", "default");
  }, [transitionTo]);

  const handleExit = useCallback(() => {
    if (confirmExitRef.current) {
      onExit();
    } else {
      setConfirmExit(true);
      setTimeout(() => setConfirmExit(false), 3000);
    }
  }, [onExit]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const s = stepRef.current;
      switch (e.key) {
        case "ArrowRight":
        case " ":
          e.preventDefault();
          if (s === "showing_problem") setStep("showing_hint");
          else if (s === "showing_hint") setStep("revealing_answer");
          else if (s === "showing_explanation") handleNext();
          break;
        case "ArrowLeft":
          e.preventDefault();
          handlePrev();
          break;
        case "1":
          if (s === "revealing_answer") handleMarkResponse("mostly_correct");
          break;
        case "2":
          if (s === "revealing_answer") handleMarkResponse("mixed");
          break;
        case "3":
          if (s === "revealing_answer") handleMarkResponse("mostly_wrong");
          break;
        case "Escape":
          handleExit();
          break;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleNext, handlePrev, handleMarkResponse, handleExit]);

  if (!problem) return null;

  const sky = skyStyles[skyKey];
  const problemFontSize = problem.problem.length > 28
    ? "clamp(2rem, 4vw, 4.5rem)"
    : problem.problem.length > 16
      ? "clamp(2.6rem, 6vw, 5.8rem)"
      : "clamp(3.4rem, 9vw, 7.5rem)";

  return (
    <div className="fixed -top-[73px] left-0 right-0 z-[1000] flex h-[calc(100vh+73px)] min-h-[calc(100vh+73px)] flex-col overflow-hidden bg-[#08120f] text-white select-none" onMouseMove={resetIdle}>
      {/* Sky */}
      <div className={`absolute inset-0 ${sky.bg} transition-all duration-[1200ms] ease-in-out`} />

      {/* Ambient light */}
      <div className="absolute inset-x-0 top-0 h-[40%] pointer-events-none overflow-hidden opacity-60">
        <div className="absolute top-[8%] left-[10%] w-32 h-12 bg-white/30 rounded-full blur-xl" style={{ animation: "cloud-drift 40s linear infinite" }} />
        <div className="absolute top-[15%] left-[50%] w-40 h-14 bg-white/20 rounded-full blur-2xl" style={{ animation: "cloud-drift 55s 10s linear infinite" }} />
        <div className="absolute top-[5%] left-[75%] w-24 h-10 bg-white/25 rounded-full blur-xl" style={{ animation: "cloud-drift 35s 5s linear infinite" }} />
      </div>

      {/* Background trees silhouette */}
      <div className="absolute bottom-[25%] left-0 right-0 h-[30%] pointer-events-none">
        <svg viewBox="0 0 1200 200" className="w-full h-full opacity-30" preserveAspectRatio="xMidYMax slice">
          <ellipse cx="100" cy="180" rx="40" ry="60" fill="#15803d" />
          <rect x="95" y="140" width="10" height="40" rx="2" fill="#6b5535" />
          <ellipse cx="250" cy="170" rx="50" ry="70" fill="#166534" />
          <rect x="245" y="130" width="10" height="40" rx="2" fill="#6b5535" />
          <ellipse cx="950" cy="175" rx="45" ry="65" fill="#15803d" />
          <rect x="945" y="135" width="10" height="40" rx="2" fill="#6b5535" />
          <ellipse cx="1100" cy="180" rx="35" ry="55" fill="#166534" />
          <rect x="1095" y="145" width="10" height="35" rx="2" fill="#6b5535" />
        </svg>
      </div>

      {/* Ground layers */}
      <div className="absolute bottom-0 left-0 right-0 h-[28%]">
        <svg viewBox="0 0 1200 250" className="w-full h-full" preserveAspectRatio="xMidYMax slice">
          <path d="M0,50 Q60,20 150,40 Q300,65 450,30 Q600,10 750,35 Q900,55 1050,25 Q1150,15 1200,30 L1200,250 L0,250 Z" fill={sky.ground[0]} fillOpacity="0.4" />
          <path d="M0,90 Q100,70 250,85 Q450,100 650,75 Q850,60 1000,80 Q1150,90 1200,75 L1200,250 L0,250 Z" fill={sky.ground[1]} fillOpacity="0.35" />
          <path d="M0,130 Q200,115 400,125 Q600,135 800,120 Q1000,110 1200,120 L1200,250 L0,250 Z" fill={sky.ground[2]} fillOpacity="0.3" />
          {/* Grass blades */}
          {Array.from({ length: 40 }, (_, i) => (
            <line
              key={i}
              x1={i * 30 + 10}
              y1="180"
              x2={i * 30 + 8 + (i % 3 === 0 ? -3 : i % 3 === 1 ? 3 : 0)}
              y2="168"
              stroke="#22c55e"
              strokeWidth="1.5"
              strokeLinecap="round"
              opacity="0.25"
            />
          ))}
          {/* Small flowers */}
          {Array.from({ length: 8 }, (_, i) => (
            <circle key={`f${i}`} cx={80 + i * 145} cy={175 + (i % 3) * 5} r="2.5" fill={i % 2 === 0 ? "#fbbf24" : "#f472b6"} opacity="0.5" />
          ))}
        </svg>
      </div>

      {/* Sparkles on correct */}
      <AnimatePresence>
        {skyKey === "correct" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 pointer-events-none"
          >
            {sparklePositions.map((s, i) => (
              <div
                key={i}
                className="absolute rounded-full"
                style={{
                  left: s.left,
                  top: s.top,
                  width: s.size,
                  height: s.size,
                  backgroundColor: s.color,
                  opacity: 0,
                  animation: `sparkle-twinkle ${s.duration}s ${s.delay}s infinite ease-in-out`,
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content area */}
      <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-8 pb-24 pt-10">
        <div className="mb-5 flex w-full max-w-[1180px] items-center justify-between rounded-2xl border border-white/10 bg-white/10 px-5 py-3 backdrop-blur-xl">
          <div>
            <p className="text-xs text-white/55">课堂投屏模式</p>
            <p className="text-lg font-semibold text-white">六年级综合计算讲评</p>
          </div>
          <div className="flex items-center gap-3 text-sm text-white/70">
            <span>第 {currentIndex + 1} 题 / 共 {problems.length} 题</span>
            <span className="rounded-full bg-white/12 px-3 py-1 text-xs">
              {step === "showing_problem" ? "读题" : step === "showing_hint" ? "提示" : step === "revealing_answer" ? "揭示答案" : "课堂反馈"}
            </span>
          </div>
        </div>
        <AnimatePresence mode="wait">
          <motion.div
            key={cardKey}
            initial={{ opacity: 0, rotateY: 90 }}
            animate={{ opacity: 1, rotateY: 0 }}
            exit={{ opacity: 0, rotateY: -90, scale: 0.9 }}
            transition={{ type: "spring", damping: 20, stiffness: 120 }}
            className="w-full max-w-[1180px]"
            style={{ perspective: 1200 }}
          >
            <div className="relative">
              {/* Presentation board */}
              <div
                className="relative rounded-[28px] border border-white/12 px-8 py-7 shadow-2xl sm:px-12 sm:py-10"
                style={{
                  background: "linear-gradient(145deg, rgba(255,255,255,0.96) 0%, rgba(246,250,246,0.94) 100%)",
                  boxShadow: "0 28px 90px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.75)",
                }}
              >
                <div className="absolute inset-0 rounded-2xl opacity-[0.04] pointer-events-none"
                  style={{ backgroundImage: "linear-gradient(90deg, rgba(22,63,49,0.12) 1px, transparent 1px), linear-gradient(rgba(22,63,49,0.08) 1px, transparent 1px)", backgroundSize: "28px 28px" }}
                />

                {/* Header row */}
                <div className="mb-3 flex items-center gap-2 text-xs">
                  <span className="rounded-full bg-white/60 px-2.5 py-0.5 font-medium text-bark-600 backdrop-blur-sm">
                    {currentIndex + 1} / {problems.length}
                  </span>
                  {problem.target_error_code && (
                    <span className="rounded-full bg-fruit-100/80 px-2.5 py-0.5 font-medium text-fruit-700 backdrop-blur-sm">
                      {problem.target_error_code} {ERROR_LABELS[problem.target_error_code as keyof typeof ERROR_LABELS]}
                    </span>
                  )}
                  {problem.knowledge_point && (
                    <span className="hidden sm:inline text-bark-500/60 text-[10px]">
                      {problem.knowledge_point}
                    </span>
                  )}
                </div>

                {/* Problem display */}
                <div className="flex min-h-[100px] sm:min-h-[130px] items-center justify-center">
                  <motion.p
                    className="text-center font-bold leading-tight text-[#17342a]"
                    style={{ fontSize: problemFontSize }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15, duration: 0.3 }}
                  >
                    {problem.problem}
                  </motion.p>
                </div>

                {/* Hint area */}
                <AnimatePresence>
                  {(step === "showing_hint" || step === "revealing_answer" || step === "showing_explanation") && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                      animate={{ opacity: 1, height: "auto", marginBottom: 12 }}
                      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="rounded-xl border border-amber-200/60 bg-amber-50/70 px-4 py-2.5 backdrop-blur-sm">
                        <p className="text-sm text-bark-600">
                          <span className="font-semibold text-amber-700">提示</span>{" "}
                          {problem.hint}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Answer reveal */}
                <AnimatePresence>
                  {(step === "revealing_answer" || step === "showing_explanation") && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.3 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ type: "spring", damping: 16, stiffness: 180, delay: 0.1 }}
                      className="flex items-center justify-center gap-4 py-2"
                    >
                      <span className="text-base text-bark-500">答案</span>
                      <motion.span
                        className="font-bold text-primary"
                        style={{ fontSize: "clamp(2.2rem, 9vw, 4.5rem)" }}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", damping: 14, stiffness: 140, delay: 0.2 }}
                      >
                        {problem.correct_answer}
                      </motion.span>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Response buttons */}
                <AnimatePresence>
                  {step === "revealing_answer" && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{ delay: 0.4 }}
                      className="mt-3 flex justify-center gap-3 sm:gap-4"
                    >
                      {(Object.entries(RESPONSE_CONFIG) as [ClassResponse, typeof RESPONSE_CONFIG[ClassResponse]][]).map(
                        ([key, cfg], idx) => (
                          <motion.button
                            key={key}
                            onClick={() => handleMarkResponse(key)}
                            whileHover={{ scale: 1.08, y: -2 }}
                            whileTap={{ scale: 0.95 }}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 + idx * 0.1 }}
                                                  className={`flex flex-col items-center gap-1 rounded-2xl px-5 py-3 text-sm font-semibold transition-colors ring-2 ring-transparent ${
                        cfg.label === "多数对了"
                          ? "hover:ring-emerald-300"
                          : cfg.label === "一半一半"
                            ? "hover:ring-amber-300"
                            : "hover:ring-orange-300"
                      } sm:px-6 sm:py-4 ${cfg.color}`}
                          >
                            <span className="text-xl sm:text-2xl">{cfg.icon}</span>
                            <span>{cfg.label}</span>
                            <span className="text-[10px] opacity-60">按 {idx + 1}</span>
                          </motion.button>
                        ),
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Explanation after response */}
                <AnimatePresence>
                  {step === "showing_explanation" && responses[currentIndex] && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-3 space-y-2"
                    >
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-lg">{RESPONSE_CONFIG[responses[currentIndex]].icon}</span>
                        <span className="font-semibold text-bark-700">
                          班级反馈：{RESPONSE_CONFIG[responses[currentIndex]].label}
                        </span>
                      </div>
                      {problem.target_error_code && problem.target_error_code !== "E99" && (
                        <div className="rounded-xl border border-bark-200/50 bg-white/50 px-3 py-2 text-xs text-bark-600 backdrop-blur-sm">
                          <span className="font-semibold">
                            {problem.target_error_code} {ERROR_LABELS[problem.target_error_code as keyof typeof ERROR_LABELS]}
                          </span>
                          <span className="mx-1">·</span>
                          {problem.knowledge_point}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Stepping stone progress */}
      <div className="absolute bottom-16 left-0 right-0 z-10 flex justify-center">
        <div className="flex items-center gap-3">
          {problems.map((_, i) => {
            const isActive = i === currentIndex;
            const resp = responses[i];
            return (
              <motion.div
                key={i}
                animate={{
                  scale: isActive ? 1.4 : 1,
                  backgroundColor: isActive
                    ? "#22c55e"
                    : resp === "mostly_correct"
                      ? "#34d399"
                      : resp === "mostly_wrong"
                        ? "#f97316"
                        : resp === "mixed"
                          ? "#fbbf24"
                          : "rgba(255,255,255,0.45)",
                }}
                className={`h-3 w-3 rounded-full shadow-sm transition-all ${isActive ? "shadow-lg shadow-primary/40" : ""}`}
                style={isActive ? { animation: "stone-glow 2s infinite ease-in-out" } : undefined}
                transition={{ type: "spring", damping: 18, stiffness: 200 }}
              />
            );
          })}
        </div>
      </div>

      {/* Control bar */}
      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            transition={{ duration: 0.25 }}
            className="absolute bottom-0 left-0 right-0 z-20 bg-white/10 backdrop-blur-xl border-t border-white/15"
          >
            <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-3">
              {/* Left: exit */}
              <div>
                {confirmExit ? (
                  <motion.button
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    onClick={onExit}
                    className="rounded-lg bg-red-500/90 px-4 py-1.5 text-sm font-medium text-white shadow"
                  >
                    确认退出
                  </motion.button>
                ) : (
                  <button onClick={handleExit} className="text-sm text-white/50 hover:text-white/90 transition-colors">
                    退出
                  </button>
                )}
              </div>

              {/* Center: nav */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrev}
                  disabled={currentIndex === 0}
                  className="rounded-lg px-3 py-1.5 text-sm text-white/60 hover:text-white hover:bg-white/10 disabled:opacity-25 disabled:cursor-not-allowed transition-all"
                >
                  ← 上一题
                </button>

                {step === "showing_problem" && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={() => setStep("showing_hint")}
                    className="rounded-xl bg-white/20 px-5 py-2 text-sm font-medium text-white hover:bg-white/30 transition-colors shadow-sm"
                  >
                    💡 提示
                  </motion.button>
                )}
                {step === "showing_hint" && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={() => setStep("revealing_answer")}
                    className="rounded-xl bg-white/20 px-5 py-2 text-sm font-medium text-white hover:bg-white/30 transition-colors shadow-sm"
                  >
                    ✨ 答案
                  </motion.button>
                )}
                {step === "showing_explanation" && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={handleNext}
                    className="rounded-xl bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors shadow-md"
                  >
                    {isLast ? "📊 查看总结" : "下一题 →"}
                  </motion.button>
                )}

                {/* Keyboard hint */}
                <span className="hidden sm:inline text-[10px] text-white/30 ml-2">
                  {step === "showing_problem" ? "空格=提示"
                    : step === "showing_hint" ? "空格=答案"
                    : step === "revealing_answer" ? "1/2/3=反馈"
                    : "→=下一题"}
                </span>
              </div>

              {/* Right: esc hint */}
              <span className="text-[10px] text-white/30">ESC 退出</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {syncError && (
        <div className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-lg bg-red-500/90 px-4 py-2 text-sm text-white shadow-lg">
          <span>{syncError}</span>
          <button
            onClick={() => setSyncError(null)}
            className="rounded px-2 py-0.5 text-xs text-white/70 hover:text-white"
          >
            关闭
          </button>
        </div>
      )}
    </div>
  );
}
