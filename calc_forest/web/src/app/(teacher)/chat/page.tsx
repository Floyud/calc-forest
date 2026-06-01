"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ArrowLeft, TreePine } from "lucide-react";
import { GuidanceChat } from "@/components/guidance/GuidanceChat";
import { DEFAULT_STUDENT_ID } from "@/lib/config";

const WELCOME =
  "你好呀！我是计算森林的树精灵🌿 有什么计算题难住你了吗？告诉题目，我们一起想办法！";

function ChatPageInner() {
  const searchParams = useSearchParams();
  const studentId = searchParams.get("student") || DEFAULT_STUDENT_ID;
  const context = searchParams.get("context");
  const welcomeMessage = context
    ? `你好呀！我看到你遇到了这个计算问题：${context}\n\n让我们一起来分析这道题吧！一步步来，不着急 🌿`
    : WELCOME;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Refined glass header */}
      <header
        className="relative z-10 flex items-center gap-3.5 border-b px-5 py-3"
        style={{
          borderColor: "var(--tone-line)",
          background:
            "linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(250, 249, 246, 0.75) 100%)",
          backdropFilter: "blur(20px) saturate(1.15)",
          boxShadow: "0 1px 0 rgba(255, 255, 255, 0.5), 0 4px 20px rgba(90, 84, 60, 0.04)",
        }}
      >
        <Link
          href="/guidance"
          className="group flex h-8 w-8 items-center justify-center rounded-[12px] border border-[var(--tone-line)] bg-white/50 text-[var(--tone-muted)] transition-all duration-200 hover:border-forest-300 hover:bg-forest-50/80 hover:text-forest-600"
          style={{
            transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
          }}
          aria-label="返回"
        >
          <ArrowLeft className="h-[15px] w-[15px] transition-transform duration-200 group-hover:-translate-x-[1px]" />
        </Link>

        <div className="flex items-center gap-3">
          {/* Refined avatar with proper forest-100 background */}
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-100/90 shadow-sm shadow-forest-200/15 ring-1 ring-forest-200/40">
            <TreePine className="h-[16px] w-[16px] text-forest-600" />
          </div>
          <div>
            <h1 className="text-[13px] font-semibold tracking-tight text-[var(--tone-ink)]">
              树精灵辅导
            </h1>
            <p className="text-[11px] text-[var(--tone-muted)]">
              一步步陪你算清楚
            </p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-hidden">
        <GuidanceChat
          studentId={studentId}
          welcomeMessage={welcomeMessage}
          className="h-full border-0 shadow-none"
        />
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageInner />
    </Suspense>
  );
}
