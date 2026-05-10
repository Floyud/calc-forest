"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { X, ChevronRight } from "lucide-react";
import { useState, useEffect, Suspense } from "react";
import { cn } from "@/lib/utils";

const DEMO_STEPS = [
  {
    href: "/",
    label: "班级森林总览",
    desc: "查看班级整体情况和错因热力图",
    emoji: "🌲",
  },
  {
    href: "/diagnose",
    label: "错因诊断",
    desc: "录入一条作答，看AI如何分析错因",
    emoji: "🔍",
  },
  {
    href: "/classroom",
    label: "课堂模式",
    desc: "一键投屏白板，现场练习反馈",
    emoji: "📋",
  },
  {
    href: "/chat?student=S001",
    label: "AI引导对话",
    desc: "体验AI一步步引导学生理解错因",
    emoji: "💬",
  },
  {
    href: "/forest",
    label: "成长轨迹",
    desc: "查看学生的错因雷达图和成长记录",
    emoji: "📈",
  },
];

function DemoGuideInner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dismissed, setDismissed] = useState(false);

  const demo = searchParams.get("demo");
  const showGuide = demo === "1" && !dismissed;

  useEffect(() => {
    if (demo === "1") {
      setDismissed(false);
    }
  }, [demo]);

  if (!showGuide) return null;

  const fullPath = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : "");

  const currentIdx = DEMO_STEPS.findIndex((step) => {
    if (step.href === "/") return pathname === "/";
    return fullPath.startsWith(step.href.split("?")[0]);
  });

  const nextStep = currentIdx >= 0 && currentIdx < DEMO_STEPS.length - 1
    ? DEMO_STEPS[currentIdx + 1]
    : null;

  return (
    <div className="border-b border-forest-200/60 bg-gradient-to-r from-forest-50 via-warm-50 to-forest-50">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2.5">
        <div className="flex items-center gap-2 text-xs text-forest-600">
          <span className="text-base">🎯</span>
          <span className="font-medium">演示引导</span>
        </div>

        <div className="flex flex-1 items-center gap-1 overflow-x-auto">
          {DEMO_STEPS.map((step, idx) => {
            const isActive = idx === currentIdx;
            const isDone = idx < currentIdx;
            return (
              <div key={step.href} className="flex items-center gap-1">
                <Link
                  href={`${step.href}${step.href.includes("?") ? "&" : "?"}demo=1`}
                  className={cn(
                    "flex items-center gap-1.5 whitespace-nowrap rounded-md px-2.5 py-1 text-xs transition-colors",
                    isActive && "bg-forest-600 text-white font-medium",
                    isDone && "text-forest-500",
                    !isActive && !isDone && "text-muted-foreground hover:bg-forest-100",
                  )}
                >
                  <span>{isDone ? "✅" : step.emoji}</span>
                  <span>{step.label}</span>
                </Link>
                {idx < DEMO_STEPS.length - 1 && (
                  <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground/50" />
                )}
              </div>
            );
          })}
        </div>

        {nextStep && (
          <Link
            href={`${nextStep.href}${nextStep.href.includes("?") ? "&" : "?"}demo=1`}
            className="shrink-0 rounded-md bg-forest-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-forest-700"
          >
            下一步 → {nextStep.label}
          </Link>
        )}

        <button
          onClick={() => setDismissed(true)}
          className="shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-forest-100 hover:text-forest-600"
          aria-label="关闭引导"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {currentIdx >= 0 && (
        <div className="mx-auto max-w-7xl px-4 pb-2">
          <p className="text-xs text-muted-foreground">
            <span className="mr-1">{DEMO_STEPS[currentIdx].emoji}</span>
            {DEMO_STEPS[currentIdx].desc}
          </p>
        </div>
      )}
    </div>
  );
}

export function DemoGuide() {
  return (
    <Suspense fallback={null}>
      <DemoGuideInner />
    </Suspense>
  );
}
