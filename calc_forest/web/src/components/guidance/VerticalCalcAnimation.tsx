"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, RotateCcw, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

// Types

interface VerticalCalcAnimationProps {
  expression: string;
  correctAnswer: string;
  studentAnswer?: string;
  errorType?: string;
  autoPlay?: boolean;
  className?: string;
}

interface ParsedExpr {
  operator: "+" | "-";
  topStr: string;
  bottomStr: string;
  topDigits: (number | null)[];
  bottomDigits: (number | null)[];
  numCols: number;
}

interface BorrowMark {
  col: number;
  value: string;
}

interface ResultMark {
  col: number;
  value: number;
}

interface StepData {
  narration: string;
  thoughtBubble?: string;
  highlights: number[];
  borrows: BorrowMark[];
  results: ResultMark[];
  celebration?: boolean;
}

// Utilities

function parseExpression(expr: string): ParsedExpr | null {
  const clean = expr.replace(/\s/g, "").replace(/=$/, "");
  const match = clean.match(/^(\d+)([+\-])(\d+)$/);
  if (!match) return null;

  const topStr = match[1];
  const op = match[2] as "+" | "-";
  const bottomStr = match[3];
  const numCols = Math.max(topStr.length, bottomStr.length);

  return {
    operator: op,
    topStr,
    bottomStr,
    topDigits: topStr
      .padStart(numCols, " ")
      .split("")
      .map((c) => (c === " " ? null : parseInt(c, 10))),
    bottomDigits: bottomStr
      .padStart(numCols, " ")
      .split("")
      .map((c) => (c === " " ? null : parseInt(c, 10))),
    numCols,
  };
}

function colName(colIndex: number, numCols: number): string {
  const names = ["个位", "十位", "百位", "千位", "万位"];
  const pos = numCols - 1 - colIndex;
  return names[pos] ?? `第${pos + 1}位`;
}

// Subtraction step generation — handles multi-column borrow chains

function generateSubtractionSteps(
  topDigits: (number | null)[],
  bottomDigits: (number | null)[],
  numCols: number,
): StepData[] {
  const steps: StepData[] = [];
  const working = topDigits.map((d) => d ?? 0);
  const bottom = bottomDigits.map((d) => d ?? 0);

  steps.push({
    narration: "让我们一步步来计算这道减法",
    highlights: [],
    borrows: [],
    results: [],
  });

  for (let i = numCols - 1; i >= 0; i--) {
    const topVal = working[i];
    const botVal = bottom[i];

    if (botVal === 0 && topVal >= 0 && i > 0) {
      const allHigherZero = working
        .slice(0, i)
        .every((d) => d === 0) && bottom.slice(0, i).every((d) => d === 0);
      if (allHigherZero) {
        steps.push({
          narration: `${colName(i, numCols)}：${topVal}`,
          highlights: [i],
          borrows: [],
          results: [{ col: i, value: topVal }],
        });
      }
      continue;
    }

    if (topVal < botVal) {
      steps.push({
        narration: `${colName(i, numCols)}：${topVal}减${botVal}，不够减，需要借位`,
        thoughtBubble: `${topVal} < ${botVal}，不够减！`,
        highlights: [i],
        borrows: [],
        results: [],
      });

      // Walk left for first non-zero digit to borrow from
      let source = -1;
      const zeroCols: number[] = [];
      for (let j = i - 1; j >= 0; j--) {
        if (working[j] > 0) {
          source = j;
          break;
        }
        zeroCols.push(j);
      }

      if (source === -1) continue;

      for (const z of zeroCols) {
        const nextCol = z > 0 ? z - 1 : source;
        steps.push({
          narration: `${colName(z, numCols)}是0，不能借，继续向${colName(nextCol, numCols)}借`,
          highlights: [z],
          borrows: [],
          results: [],
        });
      }

      // Cascade chain: [source, ...intermediates, target]
      const chain = [source];
      for (let j = source + 1; j < i; j++) chain.push(j);
      chain.push(i);

      for (let k = 0; k < chain.length - 1; k++) {
        const lender = chain[k];
        const receiver = chain[k + 1];
        const lenderOld = working[lender];
        const receiverOld = working[receiver];

        working[lender] -= 1;
        working[receiver] += 10;

        const newBorrows: BorrowMark[] = [
          { col: lender, value: String(working[lender]) },
          { col: receiver, value: String(working[receiver]) },
        ];

        let narration: string;
        if (chain.length === 2) {
          narration = `向${colName(lender, numCols)}借1，${colName(lender, numCols)}${lenderOld}变成${working[lender]}，${colName(receiver, numCols)}变成${working[receiver]}`;
        } else if (k === 0) {
          narration = `${colName(lender, numCols)}${lenderOld}借出1，变成${working[lender]}；${colName(receiver, numCols)}得到10，变成${working[receiver]}`;
        } else {
          narration = `${colName(lender, numCols)}借出1给${colName(receiver, numCols)}，${colName(lender, numCols)}变成${working[lender]}；${colName(receiver, numCols)}变成${working[receiver]}`;
        }

        steps.push({
          narration,
          highlights: [lender, receiver],
          borrows: newBorrows,
          results: [],
        });
      }
    }

    // Compute result for this column
    const resultVal = working[i] - botVal;
    const isLastComputeCol = i === 0;

    steps.push({
      narration:
        botVal > 0
          ? `${colName(i, numCols)}：${working[i]} - ${botVal} = ${resultVal} ✓`
          : `${colName(i, numCols)}：${working[i]} ✓`,
      highlights: [i],
      borrows: [],
      results: [{ col: i, value: resultVal }],
      celebration: isLastComputeCol,
    });
  }

  steps.push({
    narration: "计算完成！做得很好！ 🌱",
    highlights: Array.from({ length: numCols }, (_, i) => i),
    borrows: [],
    results: [],
    celebration: true,
  });

  return steps;
}

// Addition step generation — handles carrying

function generateAdditionSteps(
  topDigits: (number | null)[],
  bottomDigits: (number | null)[],
  numCols: number,
): StepData[] {
  const steps: StepData[] = [];
  const top = topDigits.map((d) => d ?? 0);
  const bottom = bottomDigits.map((d) => d ?? 0);

  steps.push({
    narration: "让我们一步步来计算这道加法",
    highlights: [],
    borrows: [],
    results: [],
  });

  let carry = 0;

  for (let i = numCols - 1; i >= 0; i--) {
    const topVal = top[i];
    const botVal = bottom[i];
    const sum = topVal + botVal + carry;
    const digitResult = sum % 10;
    const newCarry = Math.floor(sum / 10);

    const parts: string[] = [];
    if (botVal > 0) parts.push(String(topVal));
    if (botVal > 0) parts.push(String(botVal));
    if (carry > 0) parts.push(`${carry}(进位)`);
    const expr = parts.length > 0 ? parts.join(" + ") : String(topVal);

    const stepBorrows: BorrowMark[] = [];
    if (newCarry > 0 && i > 0) {
      stepBorrows.push({ col: i - 1, value: "¹" });
    }

    steps.push({
      narration:
        newCarry > 0
          ? `${colName(i, numCols)}：${expr} = ${sum}，满十进一`
          : `${colName(i, numCols)}：${expr} = ${digitResult} ✓`,
      thoughtBubble: newCarry > 0 ? "满十进一！" : undefined,
      highlights: [i],
      borrows: stepBorrows,
      results: [{ col: i, value: digitResult }],
      celebration: i === 0 && newCarry === 0,
    });

    carry = newCarry;
  }

  if (carry > 0) {
    steps.push({
      narration: `最高位进${carry}，完整结果是 ${carry}...`,
      highlights: [],
      borrows: [],
      results: [],
      celebration: true,
    });
  }

  steps.push({
    narration: "计算完成！做得很好！ 🌱",
    highlights: Array.from({ length: numCols }, (_, i) => i),
    borrows: [],
    results: [],
    celebration: true,
  });

  return steps;
}

// Sub-components

const CELL_W = "w-12 sm:w-14";
const DIGIT_CLS = "font-mono text-3xl sm:text-4xl select-none";

function HighlightOverlay({ visible }: { visible: boolean }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          layoutId="col-highlight"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="absolute inset-0 rounded-lg bg-warm-100/80"
        />
      )}
    </AnimatePresence>
  );
}

function CelebrationOverlay({ visible }: { visible: boolean }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.3, 0] }}
          transition={{ duration: 1.5, repeat: 2 }}
          className="pointer-events-none absolute inset-0 rounded-2xl bg-forest-200/40"
        />
      )}
    </AnimatePresence>
  );
}

// Main component

export function VerticalCalcAnimation({
  expression,
  correctAnswer,
  studentAnswer,
  autoPlay = false,
  className,
}: VerticalCalcAnimationProps) {
  // Parse & generate steps
  const parsed = useMemo(() => parseExpression(expression), [expression]);

  const steps = useMemo(() => {
    if (!parsed) return [];
    return parsed.operator === "-"
      ? generateSubtractionSteps(
          parsed.topDigits,
          parsed.bottomDigits,
          parsed.numCols,
        )
      : generateAdditionSteps(
          parsed.topDigits,
          parsed.bottomDigits,
          parsed.numCols,
        );
  }, [parsed]);

  const totalSteps = steps.length;

  // State
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);

  // Reset when expression changes
  useEffect(() => {
    setCurrentStep(0);
    setIsPlaying(autoPlay);
  }, [expression, autoPlay]);

  // Auto-play timer
  useEffect(() => {
    if (!isPlaying) return;
    if (currentStep >= totalSteps - 1) {
      setIsPlaying(false);
      return;
    }
    const timer = setTimeout(() => setCurrentStep((s) => s + 1), 2200);
    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, totalSteps]);

  // Accumulated visual state
  const borrows = useMemo(() => {
    const map = new Map<number, string>();
    for (let i = 0; i <= currentStep && i < totalSteps; i++) {
      for (const b of steps[i].borrows) map.set(b.col, b.value);
    }
    return map;
  }, [steps, currentStep, totalSteps]);

  const results = useMemo(() => {
    const map = new Map<number, number>();
    for (let i = 0; i <= currentStep && i < totalSteps; i++) {
      for (const r of steps[i].results) map.set(r.col, r.value);
    }
    return map;
  }, [steps, currentStep, totalSteps]);

  const highlights = useMemo(() => {
    return new Set(steps[currentStep]?.highlights ?? []);
  }, [steps, currentStep]);

  const isComplete = currentStep >= totalSteps - 1;
  const stepData = steps[currentStep];
  const showCelebration = isComplete || (stepData?.celebration ?? false);

  // Handlers
  const handleNext = useCallback(() => {
    if (currentStep < totalSteps - 1) setCurrentStep((s) => s + 1);
  }, [currentStep, totalSteps]);

  const handleReplay = useCallback(() => {
    setCurrentStep(0);
    setIsPlaying(false);
  }, []);

  const togglePlay = useCallback(() => {
    if (isComplete) {
      setCurrentStep(0);
      setIsPlaying(true);
    } else {
      setIsPlaying((p) => !p);
    }
  }, [isComplete]);

  if (!parsed || totalSteps === 0) {
    return (
      <div className="rounded-xl border border-warm-200 bg-warm-50/50 p-4 text-center">
        <p className="text-sm text-muted-foreground">
          该题型的竖式动画暂不支持，请参考下方引导问题进行练习
        </p>
      </div>
    );
  }

  const { topDigits, bottomDigits, numCols, operator } = parsed;

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-parchment-200 bg-parchment-50 shadow-sm",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div
          className="relative h-full"
          style={{ width: numCols * 56 + 56 }}
        >
          <div className="absolute inset-y-0 flex" style={{ left: 56 }}>
            {topDigits.map((_, i) => (
              <div
                key={`grid-${i}`}
                className="flex items-center justify-center"
                style={{ width: 56 }}
              >
                <div className="h-full border-r border-dashed border-parchment-200/60" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <CelebrationOverlay visible={showCelebration} />

      {/* Calculation area */}
      <div className="relative px-4 pt-6 pb-4 sm:px-6">
        <div className="flex justify-center">
          <div
            className="inline-flex flex-col items-stretch"
            style={{ minWidth: numCols * 48 + 48 }}
          >
                {/* Row: Borrow / carry markers */}
            <div className="flex">
              <div className={CELL_W} />
              {topDigits.map((_, i) => (
                <div
                  key={`borrow-${i}`}
                  className={cn(CELL_W, "relative h-7 flex items-end justify-center")}
                >
                  <AnimatePresence mode="popLayout">
                    {borrows.has(i) && (
                      <motion.span
                        key={`bmark-${i}-${borrows.get(i)}`}
                        initial={{ opacity: 0, scale: 0.4, y: 6 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.4, y: -4 }}
transition={{ type: "spring", stiffness: 200, damping: 18 }}
                        className="text-sm font-bold leading-none text-volcano-500"
                      >
                        {borrows.get(i)}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>

              {/* Row: Top number */}
            <div className="flex">
              <div className={CELL_W} />
              {topDigits.map((digit, i) => (
                <div
                  key={`top-${i}`}
                  className={cn(CELL_W, "relative py-1 text-center", DIGIT_CLS)}
                >
                  <HighlightOverlay visible={highlights.has(i)} />
                  {digit !== null ? (
                    <span
                      className={cn(
                        "relative z-10 transition-colors duration-300",
                        borrows.has(i)
                          ? "text-ink-300"
                          : highlights.has(i)
                            ? "text-ink-800"
                            : "text-ink-800",
                      )}
                    >
                      {digit}
                      {borrows.has(i) && (
                        <motion.span
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: 1 }}
                          transition={{ duration: 0.35, ease: "easeOut" }}
                          className="absolute left-0 top-1/2 h-[2px] w-full origin-left -translate-y-1/2 bg-volcano-400/60"
                        />
                      )}
                    </span>
                  ) : (
                    "\u00A0"
                  )}
                </div>
              ))}
            </div>

              {/* Row: Operator + Bottom number */}
            <div className="flex">
              <div
                className={cn(
                  CELL_W,
                  "py-1 text-center font-mono text-2xl text-ink-400",
                )}
              >
                {operator}
              </div>
              {bottomDigits.map((digit, i) => (
                <div
                  key={`bottom-${i}`}
                  className={cn(CELL_W, "relative py-1 text-center", DIGIT_CLS)}
                >
                  <HighlightOverlay visible={highlights.has(i)} />
                  <span
                    className={cn(
                      "relative z-10 transition-colors duration-300",
                      highlights.has(i) ? "text-ink-800" : "text-ink-500",
                    )}
                  >
                    {digit !== null ? digit : "\u00A0"}
                  </span>
                </div>
              ))}
            </div>

            {/* Row: Horizontal line */}
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
              className="my-1 h-[2px] origin-left bg-ink-400"
            />

            {/* Row: Result digits */}
            <div className="flex">
              <div className={CELL_W} />
              {topDigits.map((_, i) => (
                <div
                  key={`result-${i}`}
                  className={cn(
                    CELL_W,
                    "relative h-14 py-1 text-center flex items-center justify-center",
                    DIGIT_CLS,
                  )}
                >
                  <AnimatePresence mode="popLayout">
                    {results.has(i) && (
                      <motion.span
                        key={`res-${i}`}
                        initial={{ opacity: 0, scale: 0.2 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{
                          type: "spring",
                          stiffness: 320,
                          damping: 18,
                        }}
                        className={cn(
                          "relative z-10 font-bold",
                          highlights.has(i)
                            ? "text-forest-600"
                            : "text-forest-700",
                        )}
                      >
                        {results.get(i)}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Thought bubble */}
        <AnimatePresence mode="wait">
          {stepData?.thoughtBubble && (
            <motion.div
              key={`thought-${currentStep}`}
              initial={{ opacity: 0, y: -6, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.92 }}
              transition={{ duration: 0.25 }}
              className="mt-3 flex justify-center"
            >
              <div className="rounded-xl border border-warm-200 bg-warm-100 px-4 py-2 text-sm font-medium text-warm-500 shadow-sm">
                💭 {stepData.thoughtBubble}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Narration bar */}
      <div className="border-t border-parchment-200 bg-parchment-100/80 px-4 py-3">
        <AnimatePresence mode="wait">
          <motion.p
            key={`narr-${currentStep}`}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.25 }}
            className="text-center text-sm leading-relaxed text-ink-500"
          >
            {stepData?.narration}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between border-t border-parchment-200 bg-parchment-100/50 px-4 py-2">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={togglePlay}
            className="h-8 w-8 p-0 text-ink-400 hover:text-ink-600"
            aria-label={isPlaying ? "暂停" : "播放"}
          >
            {isPlaying ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReplay}
            className="h-8 w-8 p-0 text-ink-400 hover:text-ink-600"
            aria-label="重播"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Progress dots */}
        <div className="flex items-center gap-1">
          {steps.map((_, i) => (
            <motion.div
              key={i}
              animate={{
                width: i === currentStep ? 8 : 5,
                height: i === currentStep ? 8 : 5,
                backgroundColor:
                  i === currentStep
                    ? "var(--color-forest-500)"
                    : i < currentStep
                      ? "var(--color-forest-300)"
                      : "var(--color-parchment-300)",
              }}
              transition={{ duration: 0.2 }}
              className="rounded-full"
            />
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleNext}
          disabled={isComplete}
          className={cn(
            "h-8 w-8 p-0",
            isComplete
              ? "text-parchment-300"
              : "text-ink-400 hover:text-ink-600",
          )}
          aria-label="下一步"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Result comparison */}
      <AnimatePresence>
        {isComplete && studentAnswer && studentAnswer !== correctAnswer && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="border-t border-parchment-200 bg-white/60 px-4 py-3">
              <div className="flex items-center justify-center gap-8 text-sm">
                <div className="text-center">
                  <span className="mb-0.5 block text-xs text-muted-foreground">
                    正确答案
                  </span>
                  <span className="font-mono text-xl font-bold text-forest-600">
                    {correctAnswer}
                  </span>
                </div>
                <div className="text-center">
                  <span className="mb-0.5 block text-xs text-muted-foreground">
                    你的答案
                  </span>
                  <span className="font-mono text-xl font-bold text-volcano-500">
                    {studentAnswer} ✗
                  </span>
                </div>
                {(() => {
                  const diff = Math.abs(
                    parseInt(correctAnswer, 10) - parseInt(studentAnswer, 10),
                  );
                  if (!isNaN(diff) && diff > 0) {
                    return (
                      <span className="text-xs text-muted-foreground">
                        相差 {diff}
                      </span>
                    );
                  }
                  return null;
                })()}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
