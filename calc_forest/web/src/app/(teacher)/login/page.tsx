"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { TreePine } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

type LoginPhase = "auto" | "welcome" | "error";

const phaseVariants = {
  enter: { opacity: 0, y: 12, filter: "blur(4px)" },
  center: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -8, filter: "blur(2px)" },
};

const phaseTransition = {
  duration: 0.35,
  ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
};

export default function LoginPage() {
  const { teacher, login } = useAuth();
  const router = useRouter();
  const [phase, setPhase] = useState<LoginPhase>("auto");
  const [errorMsg, setErrorMsg] = useState("");
  const [welcomeName, setWelcomeName] = useState("");

  useEffect(() => {
    if (teacher) {
      router.replace("/");
      return;
    }

    let cancelled = false;

    async function autoLogin() {
      try {
        const t = await login();
        if (cancelled) return;
        setWelcomeName(t.name);
        setPhase("welcome");
        setTimeout(() => {
          if (!cancelled) router.replace("/");
        }, 500);
      } catch (err) {
        if (cancelled) return;
        setErrorMsg(err instanceof Error ? err.message : "连接失败，请检查后端服务");
        setPhase("error");
      }
    }

    autoLogin();
    return () => {
      cancelled = true;
    };
  }, [teacher, login, router]);

  return (
    <div className="relative flex min-h-[calc(100vh-8rem)] items-center justify-center overflow-hidden px-4">
      {/* Layered forest gradient background */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(122, 164, 113, 0.10) 0%, transparent 70%), " +
            "radial-gradient(ellipse 50% 80% at 20% 80%, rgba(93, 158, 78, 0.06) 0%, transparent 60%), " +
            "radial-gradient(ellipse 40% 50% at 85% 20%, rgba(217, 185, 107, 0.05) 0%, transparent 50%), " +
            "linear-gradient(170deg, var(--tone-paper-strong) 0%, rgba(244, 239, 226, 0.6) 100%)",
        }}
      />

      {/* Subtle dot grid texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            "radial-gradient(circle, var(--tone-ink) 0.6px, transparent 0.6px)",
          backgroundSize: "20px 20px",
        }}
      />

      {/* TreePine watermark behind the card */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <TreePine
          className="h-[340px] w-[340px] text-forest-200/[0.07]"
          strokeWidth={0.8}
        />
      </div>

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-[380px] overflow-hidden rounded-[24px] surface-glass"
      >
        {/* Gradient accent bar */}
        <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-forest-400 via-[var(--tone-accent)] to-forest-500" />

        {/* Subtle radial glow behind icon area */}
        <div className="absolute -top-8 left-1/2 h-28 w-28 -translate-x-1/2 rounded-full bg-forest-300/15 blur-3xl" />

        <div className="relative px-8 pt-14 pb-10">
          {/* Icon */}
          <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-[18px] border border-forest-200/50 bg-forest-50/70 shadow-sm shadow-forest-200/20 backdrop-blur-sm">
            <TreePine className="h-7 w-7 text-forest-600" />
          </div>

          {/* Title block */}
          <h1 className="mb-1.5 text-center text-2xl font-semibold tracking-tight text-forest-800">
            我的计算森林
          </h1>
          <p className="mb-9 text-center text-[13px] tracking-wide text-[var(--tone-muted)]">
            教师工作台
          </p>

          <AnimatePresence mode="wait">
            {phase === "auto" && (
              <motion.div
                key="auto"
                variants={phaseVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={phaseTransition}
                className="flex flex-col items-center gap-5 py-6"
              >
                {/* Softer, branded spinner */}
                <div className="relative h-6 w-6">
                  <div className="absolute inset-0 rounded-full bg-forest-200/40" />
                  <div className="absolute inset-0 animate-spin rounded-full border-[2.5px] border-transparent border-t-forest-500 border-r-forest-400/40" />
                </div>
                <p className="text-[13px] text-[var(--tone-muted)]">
                  正在自动登录...
                </p>
              </motion.div>
            )}

            {phase === "welcome" && (
              <motion.div
                key="welcome"
                variants={phaseVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={phaseTransition}
                className="flex flex-col items-center gap-3 py-6"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-forest-100/80 shadow-sm shadow-forest-200/20">
                  <TreePine className="h-5 w-5 text-forest-600" />
                </div>
                <p className="text-sm font-medium text-forest-700">
                  欢迎回来，{welcomeName}
                </p>
              </motion.div>
            )}

            {phase === "error" && (
              <motion.div
                key="error"
                variants={phaseVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={phaseTransition}
                className="flex flex-col items-center gap-5 py-4"
              >
                {/* Gentle volcano-toned error */}
                <div className="rounded-[14px] border border-amber-200/60 bg-amber-50/60 px-4 py-3">
                  <p className="text-center text-[13px] leading-6 text-amber-700/90">
                    {errorMsg}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setPhase("auto");
                    setErrorMsg("");
                    login()
                      .then((t) => {
                        setWelcomeName(t.name);
                        setPhase("welcome");
                        setTimeout(() => router.replace("/"), 500);
                      })
                      .catch((err) => {
                        setErrorMsg(
                          err instanceof Error ? err.message : "连接失败",
                        );
                        setPhase("error");
                      });
                  }}
                  className="rounded-[14px] bg-forest-600 px-7 py-2.5 text-[13px] font-medium text-white transition-all duration-200 hover:-translate-y-[1px] hover:bg-forest-700 hover:shadow-md hover:shadow-forest-300/25 active:scale-[0.98] active:bg-forest-800"
                  style={{
                    transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                >
                  重试登录
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer bar */}
        <div className="border-t border-forest-100/40 bg-forest-50/20 px-8 py-3.5 text-center text-[11px] tracking-wide text-[var(--tone-muted)]/60">
          开发模式 · 自动登录
        </div>
      </motion.div>
    </div>
  );
}
