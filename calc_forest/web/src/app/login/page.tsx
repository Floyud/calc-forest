"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TreePine } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

type LoginPhase = "auto" | "welcome" | "error";

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
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4">
      <div className="relative w-full max-w-sm overflow-hidden rounded-2xl border border-forest-200 bg-white shadow-xl shadow-forest-200/20">
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-forest-400 via-warm-400 to-forest-500" />

        <div className="relative px-8 pt-12 pb-10">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-forest-200 bg-forest-50 shadow-sm">
            <TreePine className="h-8 w-8 text-forest-600" />
          </div>

          <h1 className="mb-2 text-center text-2xl font-semibold text-forest-800">
            我的计算森林
          </h1>
          <p className="mb-8 text-center text-sm text-muted-foreground">
            教师工作台
          </p>

          {phase === "auto" && (
            <div className="flex flex-col items-center gap-4 py-6">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-forest-300 border-t-forest-600" />
              <p className="text-sm text-muted-foreground">正在自动登录…</p>
            </div>
          )}

          {phase === "welcome" && (
            <div className="flex flex-col items-center gap-3 py-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-forest-100">
                <TreePine className="h-6 w-6 text-forest-600" />
              </div>
              <p className="text-base font-medium text-forest-700">
                欢迎回来，{welcomeName}
              </p>
            </div>
          )}

          {phase === "error" && (
            <div className="flex flex-col items-center gap-4 py-4">
              <p className="text-center text-sm text-volcano-500">{errorMsg}</p>
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
                className="rounded-lg bg-forest-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-forest-700 active:bg-forest-800"
              >
                重试登录
              </button>
            </div>
          )}
        </div>

        <div className="border-t border-forest-100 bg-forest-50/50 px-8 py-4 text-center text-xs text-muted-foreground">
          开发模式 · 自动登录
        </div>
      </div>
    </div>
  );
}
