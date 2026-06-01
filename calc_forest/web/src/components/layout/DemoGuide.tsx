"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { X, ChevronRight, Compass } from "lucide-react";
import { useState, useEffect, Suspense } from "react";
import { cn } from "@/lib/utils";
import { DEMO_STEPS } from "@/lib/presentation";

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
    <div className="border-b border-[color:var(--tone-line)] bg-[linear-gradient(90deg,rgba(255,252,245,0.96),rgba(244,239,226,0.82),rgba(255,252,245,0.96))]">
      <div className="mx-auto flex max-w-[1440px] items-center gap-3 px-4 py-3 md:px-6">
        <div className="flex items-center gap-2 text-xs text-[var(--tone-accent-strong)]">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/75 ring-1 ring-[color:var(--tone-line)]">
            <Compass className="h-3.5 w-3.5" />
          </span>
          <span className="font-medium tracking-[0.12em] uppercase">演示路径</span>
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
                    "flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-xs transition-all",
                    isActive && "bg-[var(--tone-accent-strong)] text-white shadow-[0_10px_24px_rgba(74,117,81,0.22)]",
                    isDone && "bg-white/80 text-[var(--tone-accent-strong)] ring-1 ring-[color:var(--tone-line)]",
                    !isActive && !isDone && "text-[var(--tone-muted)] hover:bg-white/80",
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
            className="shrink-0 rounded-full bg-[var(--tone-accent-strong)] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:opacity-90"
          >
            下一步 → {nextStep.label}
          </Link>
        )}

        <button
          onClick={() => setDismissed(true)}
          className="shrink-0 rounded-full p-1.5 text-[var(--tone-muted)] transition-colors hover:bg-white/80 hover:text-[var(--tone-ink)]"
          aria-label="关闭引导"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {currentIdx >= 0 && (
        <div className="mx-auto max-w-[1440px] px-4 pb-3 md:px-6">
          <p className="text-xs text-[var(--tone-muted)]">
            <span className="mr-1">{DEMO_STEPS[currentIdx].emoji}</span>
            {DEMO_STEPS[currentIdx].description}
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
