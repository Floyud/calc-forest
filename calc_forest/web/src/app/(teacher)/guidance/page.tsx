"use client";

import { useState, Suspense, Fragment } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Heart,
  BookOpen,
  Lightbulb,
  Pencil,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  TreePine,
  ChevronDown,
  Sparkles,
  MessageCircle,
  RotateCcw,
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
import { cn } from "@/lib/utils";

const VerticalCalcAnimation = dynamic(
  () =>
    import("@/components/guidance/VerticalCalcAnimation").then(
      (m) => m.VerticalCalcAnimation,
    ),
  { ssr: false },
);

interface GuidanceContent {
  label: string;
  step2Title: string;
  step2Questions: string[];
  step3Key: string;
  exampleProblems: string[];
}

interface Scenario {
  problem: string;
  correct: string;
  answer: string;
  error: string;
}

const GUIDANCE_CONTENT: Record<string, GuidanceContent> = {
  E01: {
    label: "基础事实",
    step2Title: "口诀回顾",
    step2Questions: [
      "这一步对应的是哪句口诀？",
      "你能把这一个小步单独算一遍吗？",
      "3\u00d77=21, 4\u00d78=32, 想想你的那一步对应哪句？",
    ],
    step3Key: "基础算式要准确，口诀背熟不着急",
    exampleProblems: ["6\u00d78=", "7\u00d79=", "45\u00f79="],
  },
  E02: {
    label: "进位错误",
    step2Title: "找到满十的地方",
    step2Questions: [
      "哪一位相加超过了9？",
      "满十以后，你有没有把进的1加到前一位？",
      "我们一位一位看，个位先算\u2014\u2014进了几？",
    ],
    step3Key: "满十进一，进的1别忘了加到前一位",
    exampleProblems: ["28+35=", "467+278=", "1584+936="],
  },
  E03: {
    label: "退位错误",
    step2Title: "找到不够减的那一位",
    step2Questions: [
      "个位够减吗？2-8不够，怎么办？",
      "借1之后个位变成多少减多少？",
      "十位本来就是0，被借走1之后呢？",
      "百位的4被借走1变成几？",
    ],
    step3Key: "哪一位不够减就借1，借完之后前一位要少1",
    exampleProblems: ["302-168=", "501-237=", "1000-463="],
  },
  E04: {
    label: "数位对齐",
    step2Title: "检查每一位对齐了吗",
    step2Questions: [
      "个位和个位对齐了吗？十位呢？",
      "小数点的位置一致吗？",
      "把两个数按位写下来，上下对齐看看",
    ],
    step3Key: "数位对齐是计算的第一步，对不齐就会算错",
    exampleProblems: ["3.14+2.6=", "125+38=", "45.7-3.21="],
  },
  E05: {
    label: "运算顺序",
    step2Title: "找到应该先算的部分",
    step2Questions: [
      "这道题里，应该先算乘除还是加减？",
      "你能把最先算的部分圈出来吗？",
      "先算5\u00d72=10，再算3+10=？",
    ],
    step3Key: "先乘除后加减，有括号先算括号",
    exampleProblems: ["3+5\u00d72=", "12-4\u00f72=", "6+3\u00d74-8="],
  },
  E06: {
    label: "小数点/分数单位",
    step2Title: "看看小数点在哪里",
    step2Questions: [
      "八折就是80%，用小数表示是多少？",
      "240\u00d70.65，先算240\u00d765=15600，小数点应该在哪儿？",
      "小数点往左移两位，15600变成多少？",
    ],
    step3Key: "小数乘法先按整数算，最后再定小数点位置",
    exampleProblems: ["240\u00d70.65=", "3.5\u00d70.4=", "八折=？%"],
  },
  E07: {
    label: "抄写转写",
    step2Title: "对比原题和你写的",
    step2Questions: [
      "你抄下来的数字和原题一样吗？",
      "符号有没有看错？+写成-了？",
      "把原题和你的算式对比一下，找出不一样的地方",
    ],
    step3Key: "抄题要仔细，一个数字错全部错",
    exampleProblems: ["抄写检查练习"],
  },
  E08: {
    label: "步骤遗漏",
    step2Title: "检查每一步都写了吗",
    step2Questions: [
      "圆锥体积的公式是什么？你写的少了哪一步？",
      "\u03c0r\u00b2h算出来之后，还需要做什么？",
      "圆锥和圆柱体积差在哪里？",
    ],
    step3Key: "写完整算式，每一步都不能省",
    exampleProblems: ["圆锥体积：r=3, h=10", "圆柱表面积：r=2, h=5"],
  },
  E09: {
    label: "算理理解",
    step2Title: "想想为什么这样做",
    step2Questions: [
      "r\u00b2是什么意思？是r\u00d72还是r\u00d7r？",
      "面积公式里的\u03c0是从哪来的？",
      "你能画个图帮我理解吗？",
    ],
    step3Key: "理解算理比记住公式更重要",
    exampleProblems: ["圆面积：r=5", "圆柱体积：r=3, h=8"],
  },
  E10: {
    label: "审题",
    step2Title: "再读一遍题目",
    step2Questions: [
      "题目问的是什么？你确定看清楚了？",
      "有没有隐藏条件你没注意到？",
      "用笔把关键词画出来",
    ],
    step3Key: "审题是解题的第一步，看清楚再动笔",
    exampleProblems: ["应用题审题练习"],
  },
  E11: {
    label: "未验算",
    step2Title: "算完再检查一遍",
    step2Questions: [
      "你算出来的答案合理吗？1000-463=1537？",
      "能用估算检查吗？1000-500大约是500，1537对吗？",
      "用逆运算检查：1537+463=？",
    ],
    step3Key: "算完一定要检查，估算是最快的验算方法",
    exampleProblems: [
      "验算：402-178=334对吗？",
      "验算：240\u00d70.65=1560对吗？",
    ],
  },
};

const DEMO_EXAMPLES: (Scenario & { label: string; description: string })[] = [
  {
    label: "退位减法",
    problem: "402-178=",
    correct: "224",
    answer: "334",
    error: "E03",
    description: "忘记百位借位",
  },
  {
    label: "小数乘法",
    problem: "240\u00d70.65=",
    correct: "156",
    answer: "1560",
    error: "E06",
    description: "小数点位置错误",
  },
  {
    label: "圆锥体积",
    problem: "圆锥体积(r=3,h=10)",
    correct: "94.2",
    answer: "282.6",
    error: "E08",
    description: "漏了\u00f73",
  },
  {
    label: "运算顺序",
    problem: "3+5\u00d72=",
    correct: "13",
    answer: "16",
    error: "E05",
    description: "先算了加法",
  },
];

const STEP_STYLES = [
  {
    text: "text-rose-500",
    bg: "bg-rose-50",
    border: "border-rose-200",
    activeBg: "bg-rose-500",
    icon: Heart,
  },
  {
    text: "text-forest-600",
    bg: "bg-forest-50",
    border: "border-forest-200",
    activeBg: "bg-forest-500",
    icon: BookOpen,
  },
  {
    text: "text-warm-500",
    bg: "bg-warm-50",
    border: "border-warm-200",
    activeBg: "bg-warm-500",
    icon: Lightbulb,
  },
  {
    text: "text-sky-500",
    bg: "bg-sky-50",
    border: "border-sky-200",
    activeBg: "bg-sky-500",
    icon: Pencil,
  },
];

const STEP_LABELS = ["接纳安抚", "算理引导", "总结方法", "巩固练习"];

const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1];

function GuidancePageInner() {
  const searchParams = useSearchParams();

  const urlProblem = searchParams.get("problem");
  const urlScenario: Scenario | null = urlProblem
    ? {
        problem: urlProblem,
        correct: searchParams.get("correct") ?? "",
        answer: searchParams.get("answer") ?? "",
        error: searchParams.get("error") ?? "E03",
      }
    : null;

  const [scenario, setScenario] = useState<Scenario | null>(
    urlScenario ?? {
      problem: "402-178=",
      correct: "224",
      answer: "334",
      error: "E03",
    },
  );
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(
    new Set(),
  );
  const [revealedQuestions, setRevealedQuestions] = useState(0);

  const content = scenario
    ? (GUIDANCE_CONTENT[scenario.error] ?? GUIDANCE_CONTENT["E03"])
    : null;
  const stepStyle = STEP_STYLES[activeStep] ?? STEP_STYLES[0];
  const isLastStep = activeStep === 3;
  const allComplete = completedSteps.size === 4;
  const chatHref = scenario
    ? `/chat?student=S001&context=${encodeURIComponent(scenario.error + " " + scenario.problem)}`
    : "/chat";

  function selectExample(ex: (typeof DEMO_EXAMPLES)[number]) {
    setScenario({
      problem: ex.problem,
      correct: ex.correct,
      answer: ex.answer,
      error: ex.error,
    });
    setActiveStep(0);
    setCompletedSteps(new Set());
    setRevealedQuestions(0);
  }

  function handleNext() {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      next.add(activeStep);
      return next;
    });
    if (activeStep < 3) {
      setActiveStep((s) => s + 1);
      setRevealedQuestions(0);
    }
  }

  function handlePrev() {
    if (activeStep > 0) {
      setActiveStep((s) => s - 1);
      setRevealedQuestions(0);
    }
  }

  function handleReset() {
    setActiveStep(0);
    setCompletedSteps(new Set());
    setRevealedQuestions(0);
  }

  function handleRevealNext() {
    if (content && revealedQuestions < content.step2Questions.length - 1) {
      setRevealedQuestions((c) => c + 1);
    }
  }

  function goToStep(i: number) {
    setActiveStep(i);
    setRevealedQuestions(0);
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight md:text-3xl text-[var(--tone-ink)]">
          学生引导演示
        </h1>
        <p className="max-w-xl text-sm leading-relaxed text-[var(--tone-muted)]">
          体验四步引导法的完整流程：每一步只呈现一个重点，陪着孩子想清楚，不直接给答案。
        </p>
      </header>

      {/* Example selector */}
      <div className="mb-8">
        <p className="mb-3 text-[13px] font-medium text-[var(--tone-muted)]">
          选择一个典型错题，开始引导体验：
        </p>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {DEMO_EXAMPLES.map((ex) => {
            const isActive =
              scenario?.error === ex.error && scenario?.problem === ex.problem;
            return (
              <button
                key={ex.error}
                onClick={() => selectExample(ex)}
                className={cn(
                  "group relative rounded-[16px] p-3.5 text-left transition-all duration-300",
                  "surface-panel",
                  isActive
                    ? "bg-forest-50 ring-1 ring-forest-200 shadow-sm"
                    : "hover:translate-y-[-2px] hover:shadow-md hover:shadow-forest-200/15",
                )}
              >
                <Badge
                  className={cn(
                    "mb-1.5 text-[10px]",
                    isActive
                      ? "bg-forest-200 text-forest-800"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  {ex.error}
                </Badge>
                <p className="text-sm font-semibold leading-tight tracking-tight text-[var(--tone-ink)]">
                  {ex.label}
                </p>
                <p className="mt-1 text-[11px] text-[var(--tone-muted)]">
                  {ex.description}
                </p>
                <p className="mt-1.5 font-mono text-[11px] text-[var(--tone-muted)]">
                  {ex.problem}{" "}
                  <span className="text-warm-400">&rarr;</span> {ex.answer}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {!scenario && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: EASE_OUT }}
          className="rounded-[16px] border border-dashed border-forest-200 bg-forest-50/30 p-8 text-center"
        >
          <TreePine className="mx-auto mb-3 h-10 w-10 text-forest-300" />
          <p className="text-[13px] text-forest-600">
            点击上方的错题卡片，或从{" "}
            <Link
              href="/diagnose"
              className="underline underline-offset-2 hover:text-forest-800"
            >
              诊断页面
            </Link>{" "}
            跳转，开始四步引导体验。
          </p>
        </motion.div>
      )}

      {scenario && content && (
        <>
          {/* Context bar — scenario info */}
          <div className="mb-7 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-[16px] surface-soft px-5 py-3.5">
            <Badge className="bg-forest-100 text-forest-700">
              {scenario.error}
            </Badge>
            <span className="font-mono text-[13px] font-medium text-[var(--tone-ink)]">
              {scenario.problem}
            </span>
            <span className="hidden text-[var(--tone-line)] sm:inline">|</span>
            <span className="text-[13px]">
              你的答案：
              <span className="font-mono font-semibold text-volcano-500">
                {scenario.answer}
              </span>
            </span>
            <span className="hidden text-[var(--tone-line)] sm:inline">|</span>
            <span className="text-[13px]">
              正确答案：
              <span className="font-mono font-semibold text-forest-600">
                {scenario.correct}
              </span>
            </span>
          </div>

          {/* Step indicator — redesigned stepper */}
          <div className="mb-9 flex items-start">
            {STEP_STYLES.map((sc, i) => {
              const IconComp = sc.icon;
              const isActive = i === activeStep;
              const isComplete = completedSteps.has(i);
              return (
                <Fragment key={i}>
                  <button
                    onClick={() => goToStep(i)}
                    className="group flex flex-col items-center gap-1.5"
                  >
                    <div
                      className={cn(
                        "flex items-center justify-center transition-all duration-300",
                        isActive && `${sc.activeBg} text-white rounded-full px-3 h-8 shadow-sm`,
                        isComplete &&
                          !isActive &&
                          "bg-forest-100 text-forest-600 rounded-full h-8 w-8",
                        !isComplete &&
                          !isActive &&
                          "bg-muted/40 text-muted-foreground/40 rounded-full h-8 w-8",
                      )}
                    >
                      {isComplete && !isActive ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : isActive ? (
                        <IconComp className="h-4 w-4" />
                      ) : (
                        <IconComp className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <span
                      className={cn(
                        "text-[11px] font-medium transition-colors duration-200",
                        isActive
                          ? "text-[var(--tone-ink)]"
                          : "text-[var(--tone-muted)]",
                      )}
                    >
                      {STEP_LABELS[i]}
                    </span>
                  </button>
                  {i < 3 && (
                    <div
                      className={cn(
                        "mx-1.5 mt-3 h-px flex-1 transition-colors duration-300 md:mx-2",
                        i < activeStep
                          ? "bg-forest-300"
                          : "bg-[var(--tone-line)]",
                      )}
                    />
                  )}
                </Fragment>
              );
            })}
          </div>

          {/* Step content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3, ease: EASE_OUT }}
            >
              {/* Step 1: 接纳安抚 */}
              {activeStep === 0 && (
                <div className="surface-panel rounded-[16px]">
                  <div className="border-b border-[var(--tone-line)] px-6 py-5">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex h-10 w-10 items-center justify-center rounded-[14px]", stepStyle.bg)}>
                        <Heart className={cn("h-5 w-5", stepStyle.text)} />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold tracking-tight text-[var(--tone-ink)]">接纳安抚</h2>
                        <p className="text-sm text-[var(--tone-muted)]">
                          让学生知道出错是正常的，降低紧张感
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-5 px-6 py-5">
                    <div className="flex items-center justify-center gap-6 rounded-[14px] bg-white/60 p-6">
                      <div className="text-center">
                        <p className="mb-1 text-[11px] text-[var(--tone-muted)]">题目</p>
                        <p className="font-mono text-lg font-semibold text-[var(--tone-ink)]">
                          {scenario.problem}
                        </p>
                      </div>
                      <div className="flex flex-col items-center gap-1">
                        <div className="text-center">
                          <p className="mb-1 text-[11px] text-[var(--tone-muted)]">你的答案</p>
                          <p className="font-mono text-lg font-semibold text-volcano-500">
                            {scenario.answer}
                          </p>
                        </div>
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-forest-100">
                          <TreePine className="h-3 w-3 text-forest-600" />
                        </div>
                        <div className="text-center">
                          <p className="mb-1 text-[11px] text-[var(--tone-muted)]">正确答案</p>
                          <p className="font-mono text-lg font-semibold text-forest-600">
                            {scenario.correct}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className={cn("rounded-[14px] p-4", stepStyle.bg)}>
                      <p className="text-[13px] leading-relaxed md:text-sm">
                        没关系，我们一起来看看这道题。计算出错是很正常的事情，重要的是我们一起来找到哪里可以更好。
                      </p>
                    </div>

                    <div className="flex items-start gap-2.5 rounded-[14px] bg-bark-50/60 p-3.5 text-[13px]">
                      <TreePine className="mt-0.5 h-4 w-4 shrink-0 text-bark-500" />
                      <span className="text-bark-600">
                        先安抚情绪，再引导思考。不要一上来就指出错误。
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: 算理引导 (HERO STEP) */}
              {activeStep === 1 && (
                <div className="surface-panel rounded-[16px] border-2 border-forest-300 shadow-lg shadow-forest-200/30">
                  <div className="border-b border-forest-200/60 px-6 py-5">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-forest-100">
                        <BookOpen className="h-5 w-5 text-forest-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h2 className="text-lg font-semibold tracking-tight text-[var(--tone-ink)]">算理引导</h2>
                          <Badge className="bg-forest-100 text-forest-700">
                            {content.label}
                          </Badge>
                        </div>
                        <p className="text-sm text-[var(--tone-muted)]">
                          {content.step2Title}
                          {" "}引导学生自己发现问题
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-5 px-6 py-5">
                    <VerticalCalcAnimation
                      expression={scenario.problem.replace(/=$/, "")}
                      correctAnswer={scenario.correct}
                      studentAnswer={scenario.answer}
                      errorType={scenario.error}
                      autoPlay={false}
                    />
                    <div className="space-y-3 rounded-[14px] bg-white/50 p-5">
                      <p className="text-[11px] font-medium text-[var(--tone-muted)] uppercase tracking-wide">
                        逐步引导学生思考（点击揭示下一个问题）
                      </p>

                      {content.step2Questions.map((q, i) => {
                        const isRevealed = i <= revealedQuestions;
                        return (
                          <AnimatePresence key={i}>
                            {isRevealed && (
                              <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.35, ease: EASE_OUT }}
                                className="flex items-start gap-3"
                              >
                                <span
                                  className={cn(
                                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold",
                                    i === revealedQuestions
                                      ? "bg-forest-500 text-white"
                                      : "bg-forest-100 text-forest-600",
                                  )}
                                >
                                  {i + 1}
                                </span>
                                <div className="flex-1 pt-0.5">
                                  <p
                                    className={cn(
                                      "text-[13px] leading-relaxed",
                                      i === revealedQuestions
                                        ? "font-medium text-[var(--tone-ink)]"
                                        : "text-[var(--tone-muted)]",
                                    )}
                                  >
                                    {q}
                                  </p>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        );
                      })}

                      {revealedQuestions <
                        content.step2Questions.length - 1 && (
                        <Button
                          variant="outline"
                          onClick={handleRevealNext}
                          className="mt-2 w-full border-dashed border-forest-300 text-[13px] text-forest-600 hover:bg-forest-50 rounded-full"
                        >
                          <ChevronDown className="mr-1 h-3.5 w-3.5" />
                          下一个引导问题
                        </Button>
                      )}

                      {revealedQuestions >=
                        content.step2Questions.length - 1 && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.3 }}
                          className="rounded-[14px] bg-forest-50/60 p-3.5 text-center text-[13px] text-forest-600"
                        >
                          <Sparkles className="mb-1 mr-1 inline h-4 w-4" />
                          所有引导问题已揭示，学生可以自己找到答案了！
                        </motion.div>
                      )}
                    </div>

                    <div className="flex items-start gap-2.5 rounded-[14px] bg-bark-50/60 p-3.5 text-[13px]">
                      <TreePine className="mt-0.5 h-4 w-4 shrink-0 text-bark-500" />
                      <span className="text-bark-600">
                        用教材方法引导，不直接说答案。让学生自己发现错在哪里。
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: 总结方法 */}
              {activeStep === 2 && (
                <div className="surface-panel rounded-[16px]">
                  <div className="border-b border-[var(--tone-line)] px-6 py-5">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex h-10 w-10 items-center justify-center rounded-[14px]", stepStyle.bg)}>
                        <Lightbulb className={cn("h-5 w-5", stepStyle.text)} />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold tracking-tight text-[var(--tone-ink)]">总结方法</h2>
                        <p className="text-sm text-[var(--tone-muted)]">
                          帮助学生把关键点用一句话说清楚
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-5 px-6 py-5">
                    <div className={cn("rounded-[14px] p-4", stepStyle.bg)}>
                      <p className="text-[13px] leading-relaxed">
                        你能用一句话说出{content.label}
                        最关键的一步是什么吗？
                      </p>
                    </div>

                    <div className="rounded-[14px] border border-warm-200 bg-gradient-to-br from-warm-50 to-parchment-50 p-5">
                      <div className="mb-2 flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-warm-500" />
                        <span className="text-[11px] font-semibold text-warm-500 uppercase tracking-wide">
                          核心要点
                        </span>
                      </div>
                      <p className="text-sm font-semibold leading-relaxed text-[var(--tone-ink)]">
                        {content.step3Key}
                      </p>
                    </div>

                    <div className="flex items-start gap-2.5 rounded-[14px] bg-bark-50/60 p-3.5 text-[13px]">
                      <TreePine className="mt-0.5 h-4 w-4 shrink-0 text-bark-500" />
                      <span className="text-bark-600">
                        让学生用自己的话总结，比老师重复讲解更有效。
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: 巩固练习 */}
              {activeStep === 3 && (
                <div className="surface-panel rounded-[16px]">
                  <div className="border-b border-[var(--tone-line)] px-6 py-5">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex h-10 w-10 items-center justify-center rounded-[14px]", stepStyle.bg)}>
                        <Pencil className={cn("h-5 w-5", stepStyle.text)} />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold tracking-tight text-[var(--tone-ink)]">巩固练习</h2>
                        <p className="text-sm text-[var(--tone-muted)]">
                          用同类型题目巩固刚掌握的方法
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-5 px-6 py-5">
                    <p className="text-[13px] text-[var(--tone-muted)]">
                      现在用刚才学到的方法，试着做下面这几道题。不用急，一步一步写清楚：
                    </p>

                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {content.exampleProblems.map((prob, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.08, duration: 0.3, ease: EASE_OUT }}
                          className="group rounded-[14px] border border-sky-200 bg-white/60 p-4 transition-all duration-200 hover:border-sky-300 hover:shadow-sm"
                        >
                          <span className="mb-2 flex h-5 w-5 items-center justify-center rounded-full bg-sky-100 text-[11px] font-bold text-sky-600">
                            {i + 1}
                          </span>
                          <p className="font-mono text-[13px] font-medium text-[var(--tone-ink)]">
                            {prob}
                          </p>
                        </motion.div>
                      ))}
                    </div>

                    <Link
                      href={chatHref}
                      className="flex items-center gap-3 rounded-[14px] border border-forest-200 bg-gradient-to-r from-forest-50/60 to-sage-50/60 p-4 transition-all duration-200 hover:shadow-md hover:shadow-forest-200/20"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-forest-100">
                        <MessageCircle className="h-4 w-4 text-forest-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-[13px] font-semibold text-forest-800">
                          和树精灵对话
                        </p>
                        <p className="text-[11px] text-[var(--tone-muted)]">
                          遇到困难？让树精灵一步步陪你算清楚
                        </p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-forest-400" />
                    </Link>

                    <div className="flex items-start gap-2.5 rounded-[14px] bg-bark-50/60 p-3.5 text-[13px]">
                      <TreePine className="mt-0.5 h-4 w-4 shrink-0 text-bark-500" />
                      <span className="text-bark-600">
                        练习量控制在3-5分钟，重质不重量。错题不是惩罚。
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation — redesigned pills */}
          <div className="mt-7 flex items-center justify-between">
            <Button
              variant="outline"
              onClick={handlePrev}
              disabled={activeStep === 0}
              className="rounded-full transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              上一步
            </Button>

            <div className="flex gap-2">
              {activeStep === 1 && (
                <Button
                  onClick={handleNext}
                  className="rounded-full bg-forest-600 hover:bg-forest-700 transition-all duration-300"
                >
                  <Sparkles className="mr-1 h-4 w-4" />
                  我想到了！
                </Button>
              )}

              {isLastStep ? (
                <Button
                  onClick={handleReset}
                  variant="outline"
                  className="rounded-full transition-all duration-300"
                >
                  <RotateCcw className="mr-1 h-4 w-4" />
                  重新开始
                </Button>
              ) : activeStep !== 1 ? (
                <Button
                  onClick={handleNext}
                  className="rounded-full transition-all duration-300"
                >
                  下一步
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              ) : null}
            </div>
          </div>

          {/* Completion */}
          {allComplete && isLastStep && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: EASE_OUT }}
              className="mt-7 rounded-[16px] surface-soft p-6 text-center"
            >
              <TreePine className="mx-auto mb-3 h-10 w-10 text-forest-600" />
              <h3 className="mb-1 text-base font-semibold tracking-tight text-forest-800">
                四步引导完成
              </h3>
              <p className="mb-4 text-[13px] text-forest-700">
                接纳 &rarr; 引导 &rarr; 总结 &rarr;
                练习，不直接给答案，陪着孩子想清楚。
              </p>
              <div className="flex justify-center gap-3">
                <Link href="/diagnose" className="inline-flex h-9 items-center justify-center rounded-full bg-primary px-4 text-sm font-medium text-primary-foreground transition-all duration-300 hover:bg-primary/90">
                  体验完整诊断
                </Link>
                <Link href="/forest" className="inline-flex h-9 items-center justify-center rounded-full border border-border bg-background px-4 text-sm font-medium transition-all duration-300 hover:bg-muted">
                  查看森林成长
                </Link>
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* Bottom CTA */}
      <div className="mt-8">
        <Link
          href={chatHref}
          className="flex items-center gap-4 rounded-[16px] border border-forest-200 bg-gradient-to-r from-forest-50/50 to-warm-50/50 p-5 transition-all duration-300 hover:shadow-md hover:shadow-forest-200/20"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[14px] bg-forest-100">
            <TreePine className="h-5 w-5 text-forest-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-semibold tracking-tight text-forest-800">
              和树精灵对话
            </h2>
            <p className="mt-0.5 text-[13px] text-[var(--tone-muted)]">
              输入一道计算题，树精灵会一步步引导你算清楚，不直接给答案。
            </p>
          </div>
          <ArrowRight className="h-5 w-5 shrink-0 text-forest-400" />
        </Link>
      </div>
    </div>
  );
}

export default function GuidancePage() {
  return (
    <Suspense>
      <GuidancePageInner />
    </Suspense>
  );
}
