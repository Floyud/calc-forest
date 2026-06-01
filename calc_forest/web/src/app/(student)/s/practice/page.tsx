"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, X, Zap, Trophy } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export default function StudentPracticePage() {
  const router = useRouter();
  const [studentId, setStudentId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [problem, setProblem] = useState<{ problem_id: string; sequence: number; problem: string } | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<{ is_correct: boolean; correct_answer?: string; error_code?: string } | null>(null);
  const [stats, setStats] = useState({ total: 0, correct: 0 });
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState<{ total: number; correct: number; accuracy: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  const loadNextProblem = useCallback(async (sid: string, sessId: string) => {
    setAnswer("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/students/${sid}/practice/${sessId}/next`);
      if (!res.ok) {
        setPageError("无法加载题目，请重试");
        return;
      }
      const data = await res.json();
      if (data.problem_id) {
        setProblem(data);
      } else {
        setPageError("没有更多题目了");
      }
    } catch {
      setPageError("网络错误，请检查连接");
    }
  }, []);

  useEffect(() => {
    const raw = localStorage.getItem("student_session");
    if (!raw) { router.push("/s/login"); return; }
    const session = JSON.parse(raw);
    setStudentId(session.student.id);

    fetch(`${API_BASE}/api/students/${session.student.id}/practice/start`, { method: "POST" })
      .then((r) => {
        if (!r.ok) throw new Error("创建练习会话失败");
        return r.json();
      })
      .then((data) => {
        if (!data.session_id) throw new Error("无效的会话响应");
        setSessionId(data.session_id);
        return loadNextProblem(session.student.id, data.session_id);
      })
      .then(() => setPageLoading(false))
      .catch((err) => {
        setPageError(err instanceof Error ? err.message : "加载失败");
        setPageLoading(false);
      });
  }, [router, loadNextProblem]);

  const submitAnswer = async () => {
    if (!answer.trim() || !problem) return;
    setLoading(true);
    setPageError(null);
    try {
      const res = await fetch(`${API_BASE}/api/students/${studentId}/practice/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problem.problem_id, answer: answer.trim() }),
      });
      if (!res.ok) throw new Error("提交失败");
      const data = await res.json();
      setResult(data);
      setStats((s) => ({
        total: s.total + 1,
        correct: s.correct + (data.is_correct ? 1 : 0),
      }));
    } catch {
      setPageError("提交答案失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  const nextProblem = () => {
    loadNextProblem(studentId, sessionId);
  };

  const endSession = async () => {
    const res = await fetch(`${API_BASE}/api/students/${studentId}/practice/${sessionId}/end`, { method: "POST" });
    const data = await res.json();
    setSummary(data);
    setShowSummary(true);
  };

  if (pageLoading) {
    return (
      <div className="max-w-lg mx-auto px-4 py-12 text-center">
        <div className="text-3xl mb-3 animate-pulse">📐</div>
        <p className="text-sm" style={{ color: "var(--color-soft-400)" }}>正在准备题目...</p>
      </div>
    );
  }

  if (pageError && !problem) {
    return (
      <div className="max-w-lg mx-auto px-4 py-12 text-center">
        <div className="text-3xl mb-3">😔</div>
        <p className="text-sm mb-4" style={{ color: "var(--color-soft-500)" }}>{pageError}</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => router.push("/s/home")}
            className="px-4 py-2 rounded-2xl text-sm font-medium"
            style={{ background: "var(--color-sand-100)", color: "#3e3a36" }}
          >
            返回首页
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 rounded-2xl text-sm font-medium text-white"
            style={{ background: "var(--color-mist-500)" }}
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  if (showSummary && summary) {
    return (
      <div className="max-w-lg mx-auto px-4 py-6">
        <div
          className="surface-double-bezel rounded-2xl p-6 text-center"
          style={{ boxShadow: "0 16px 48px rgba(120, 115, 100, 0.1)" }}
        >
          <div
            className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, var(--color-mist-100) 0%, var(--color-mist-200) 100%)" }}
          >
            <Trophy className="w-8 h-8" style={{ color: "var(--color-mist-500)" }} />
          </div>
          <h2 className="text-2xl font-semibold mb-2" style={{ color: "#3e3a36" }}>
            练习结束！
          </h2>
          <p className="text-lg mb-1" style={{ color: "var(--color-mist-500)" }}>
            {summary.correct}/{summary.total} 题正确
          </p>
          <p className="text-3xl font-semibold mb-6" style={{ color: "var(--color-mist-500)" }}>
            {summary.accuracy}%
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/s/home")}
              className="flex-1 h-12 rounded-2xl font-medium transition-all duration-300"
              style={{
                background: "var(--color-sand-100)",
                color: "#3e3a36",
              }}
            >
              返回首页
            </button>
            <button
              onClick={() => {
                setShowSummary(false);
                setSummary(null);
                window.location.reload();
              }}
              className="flex-1 h-12 rounded-2xl font-medium text-white transition-all duration-300 active:scale-[0.97]"
              style={{ background: "var(--color-mist-500)" }}
            >
              再练一组
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={endSession}
          className="p-2 -ml-2 transition-colors duration-300"
          style={{ color: "var(--color-soft-400)" }}
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-1 text-sm">
          <Zap className="w-4 h-4" style={{ color: "var(--color-mist-500)" }} />
          <span className="font-semibold" style={{ color: "var(--color-mist-500)" }}>
            {stats.correct}
          </span>
          <span style={{ color: "var(--color-soft-400)" }}>/</span>
          <span className="font-medium" style={{ color: "#3e3a36" }}>{stats.total}</span>
          {stats.total > 0 && (
            <span className="ml-1" style={{ color: "var(--color-soft-400)" }}>
              ({Math.round((stats.correct / stats.total) * 100)}%)
            </span>
          )}
        </div>
        <button
          onClick={endSession}
          className="text-xs font-medium transition-colors duration-300"
          style={{ color: "var(--color-mist-500)" }}
        >
          结束练习
        </button>
      </div>

      {/* Error banner */}
      {pageError && problem && (
        <div className="rounded-2xl p-3 mb-4 text-center text-sm" style={{
          background: "var(--color-blush-50)",
          color: "var(--color-blush-400)",
          border: "1px solid rgba(242, 168, 171, 0.2)",
        }}>
          {pageError}
        </div>
      )}

      {/* Problem card */}
      {problem && (
        <div className="surface-soft rounded-2xl p-8 mb-6 text-center">
          <p className="text-4xl font-semibold tracking-wide" style={{ color: "#3e3a36" }}>
            {problem.problem}
          </p>
        </div>
      )}

      {result ? (
        <div className="space-y-4">
          {/* Result card */}
          <div
            className="rounded-2xl p-6 text-center"
            style={{
              background: result.is_correct
                ? "var(--color-mist-50)"
                : "var(--color-blush-50)",
              border: result.is_correct
                ? "1px solid rgba(155, 170, 200, 0.15)"
                : "1px solid rgba(242, 168, 171, 0.2)",
            }}
          >
            <div className="text-4xl mb-2">{result.is_correct ? "✅" : "❌"}</div>
            <p
              className="text-lg font-semibold"
              style={{
                color: result.is_correct
                  ? "var(--color-mist-500)"
                  : "var(--color-blush-400)",
              }}
            >
              {result.is_correct ? "回答正确！" : "再想想看"}
            </p>
            {!result.is_correct && result.correct_answer && (
              <p className="text-sm mt-1" style={{ color: "var(--color-soft-400)" }}>
                正确答案：{result.correct_answer}
              </p>
            )}
          </div>
          <button
            onClick={nextProblem}
            className="w-full h-14 rounded-2xl text-lg font-semibold text-white transition-all duration-300 active:scale-[0.97]"
            style={{ background: "var(--color-mist-500)" }}
          >
            下一题 →
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Calculator pad */}
          <div className="grid grid-cols-4 gap-2">
            {["7", "8", "9", "÷", "4", "5", "6", "×", "1", "2", "3", "-", "0", ".", "/", "+"].map(
              (key) => (
                <button
                  key={key}
                  onClick={() => setAnswer((a) => a + key)}
                  className="surface-soft h-14 rounded-2xl text-xl font-semibold transition-all duration-150 active:scale-[0.97]"
                  style={{
                    color: "#3e3a36",
                    boxShadow: "0 2px 8px rgba(90, 84, 60, 0.04)",
                  }}
                >
                  {key}
                </button>
              )
            )}
          </div>

          {/* Answer display */}
          {answer && (
            <div
              className="surface-glass rounded-2xl p-3 text-center"
              style={{
                background: "var(--color-mist-100)",
                border: "1px solid rgba(155, 170, 200, 0.15)",
              }}
            >
              <span className="text-2xl font-mono font-semibold" style={{ color: "#3e3a36" }}>
                {answer}
              </span>
              <button
                onClick={() => setAnswer("")}
                className="ml-3 text-xs underline transition-colors duration-300"
                style={{ color: "var(--color-soft-400)" }}
              >
                清除
              </button>
            </div>
          )}

          {/* Submit */}
          <button
            onClick={submitAnswer}
            disabled={!answer.trim() || loading}
            className="w-full h-14 rounded-2xl text-lg font-semibold flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-30 active:scale-[0.97]"
            style={{ background: "var(--color-mist-500)", color: "white" }}
          >
            {loading ? "..." : (
              <>
                <Check className="w-5 h-5" /> 提交答案
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
