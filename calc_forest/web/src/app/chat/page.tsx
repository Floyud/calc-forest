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

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <header className="flex items-center gap-3 border-b border-forest-200 bg-white/80 px-4 py-3 backdrop-blur-xl">
        <Link
          href="/guidance"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-forest-200 text-forest-600 transition-colors hover:bg-forest-50"
          aria-label="返回"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-forest-100">
            <TreePine className="h-4 w-4 text-forest-600" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-forest-800">
              树精灵辅导
            </h1>
            <p className="text-xs text-muted-foreground">
              一步步陪你算清楚
            </p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-hidden">
        <GuidanceChat
          studentId={studentId}
          welcomeMessage={WELCOME}
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
