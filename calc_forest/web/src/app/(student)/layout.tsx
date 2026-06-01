"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, Brain, PenTool, TreePine } from "lucide-react";
import { cn } from "@/lib/utils";
import { BackgroundBlobs } from "@/components/layout/BackgroundBlobs";
import { PageTransition } from "@/components/layout/PageTransition";

const TABS = [
  { href: "/s/home", label: "作业", icon: BookOpen },
  { href: "/s/quiz", label: "测验", icon: Brain },
  { href: "/s/practice", label: "练习", icon: PenTool },
  { href: "/s/growth", label: "我的", icon: TreePine },
];

export default function StudentLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();

  const isLoginPage = pathname === "/s/login";
  if (isLoginPage) {
    return (
      <div className="relative min-h-dvh flex items-center justify-center"
        style={{ background: "linear-gradient(160deg, var(--color-soft-50) 0%, var(--color-mist-50) 45%, var(--color-sand-50) 100%)" }}>
        <BackgroundBlobs variant="student" />
        <div className="relative" style={{ zIndex: 1 }}><PageTransition>{children}</PageTransition></div>
      </div>
    );
  }

  return (
    <div className="relative min-h-dvh"
      style={{ background: "linear-gradient(160deg, var(--color-soft-50) 0%, var(--color-mist-50) 45%, var(--color-sand-50) 100%)" }}>
      <BackgroundBlobs variant="student" />
      <div className="relative" style={{ zIndex: 1 }}>
      <div className="md:hidden flex flex-col min-h-dvh">
        <div className="flex-1 pb-20 overflow-y-auto smooth-scroll">
          <PageTransition>{children}</PageTransition>
        </div>
        <nav className="fixed bottom-0 left-0 right-0 surface-glass z-50"
          style={{ borderTop: "1px solid rgba(180, 172, 158, 0.12)" }}>
          <div className="max-w-lg mx-auto flex justify-around items-center h-16">
            {TABS.map((tab) => {
              const active = pathname.startsWith(tab.href);
              return (
                <Link key={tab.href} href={tab.href}
                  className={cn(
                    "flex flex-col items-center justify-center gap-0.5 px-3 py-1 rounded-xl min-w-[64px]",
                    "transition-all duration-300",
                    active
                      ? "text-mist-500"
                      : "text-soft-400 hover:text-soft-500"
                  )}>
                  <div className={cn(
                    "p-1.5 rounded-xl transition-all duration-300",
                    active && "bg-mist-100/60"
                  )}>
                    <tab.icon className={cn("w-5 h-5")} strokeWidth={active ? 2.5 : 1.5} />
                  </div>
                  <span className={cn("text-xs transition-all duration-300", active && "font-semibold")}>{tab.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </div>

        <div className="hidden md:flex min-h-dvh">
        <aside className="w-16 lg:w-48 shrink-0 surface-soft flex flex-col items-center lg:items-stretch py-4 sticky top-0 h-dvh z-40">
          <div className="mb-6 px-2">
            <div className="w-10 h-10 mx-auto lg:mx-2 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, var(--color-mist-400) 0%, var(--color-mist-500) 100%)" }}>
              <TreePine className="w-5 h-5 text-white" />
            </div>
            <p className="hidden lg:block text-xs font-semibold mt-2 px-2 truncate"
              style={{ color: "var(--color-mist-500)" }}>计算森林</p>
          </div>
          <nav className="flex-1 flex flex-col gap-1 px-2">
            {TABS.map((tab) => {
              const active = pathname.startsWith(tab.href);
              return (
                <Link key={tab.href} href={tab.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-300",
                    active
                      ? "bg-mist-100/60 text-mist-500"
                      : "text-soft-400 hover:bg-soft-100/60 hover:text-mist-500"
                  )}
                  style={{ fontWeight: active ? 600 : 400 }}>
                  <tab.icon className={cn("w-5 h-5 shrink-0")} strokeWidth={active ? 2.5 : 1.5} />
                  <span className={cn("hidden lg:block text-sm", active && "font-semibold")}>{tab.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="flex-1 min-h-dvh overflow-y-auto smooth-scroll">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
      </div>
    </div>
  );
}
