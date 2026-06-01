"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Send, Clock } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export default function StudentQuizPage() {
  const router = useRouter();
  const params = useParams();
  const quizId = params.id as string;
  const [studentId, setStudentId] = useState("");
  const [problems, setProblems] = useState<Array<{ sequence: number; problem: string; hint: string }>>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [submitted, setSubmitted] = useState<Record<number, boolean>>({});
  const [results, setResults] = useState<Record<number, { is_correct: boolean }>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem("student_session");
    if (!raw) { router.push("/s/login"); return; }
    const session = JSON.parse(raw);
    setStudentId(session.student.id);

    fetch(`${API_BASE}/api/quiz/${quizId}`)
      .then((r) => r.json())
      .then((data) => {
        setProblems(data.problems || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [quizId, router]);

  const submitAnswer = async () => {
    if (!answer.trim() || problems.length === 0) return;
    const seq = problems[currentIdx].sequence;
    const res = await fetch(`${API_BASE}/api/quiz/${quizId}/student-answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: studentId,
        problem_sequence: seq,
        student_answer: answer.trim(),
      }),
    });
    const data = await res.json();
    setSubmitted((prev) => ({ ...prev, [seq]: true }));
    setResults((prev) => ({ ...prev, [seq]: data }));
    setAnswer("");

    if (currentIdx < problems.length - 1) {
      setTimeout(() => setCurrentIdx((i) => i + 1), 1500);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div
            className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
            style={{ background: "var(--color-mist-100)" }}
          >
            <Clock className="w-6 h-6 animate-pulse" style={{ color: "var(--color-mist-400)" }} />
          </div>
          <p className="font-medium" style={{ color: "var(--color-mist-500)" }}>
            等待测验开始...
          </p>
        </div>
      </div>
    );
  }

  const answeredCount = Object.keys(submitted).length;
  const allDone = answeredCount === problems.length;

  if (allDone) {
    const correctCount = Object.values(results).filter((r) => r.is_correct).length;
    return (
      <div className="max-w-lg mx-auto px-4 py-6">
        <div
          className="surface-glass rounded-2xl p-6 text-center"
          style={{ boxShadow: "0 16px 48px rgba(120, 115, 100, 0.1)" }}
        >
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-2xl font-semibold" style={{ color: "#3e3a36" }}>
            测验完成！
          </h2>
          <p className="text-lg mt-2" style={{ color: "var(--color-mist-500)" }}>
            {correctCount}/{problems.length} 题正确
          </p>
          <button
            onClick={() => router.push("/s/home")}
            className="mt-6 h-12 px-8 rounded-2xl font-medium transition-all duration-300 active:scale-[0.97]"
            style={{
              background: "var(--color-sand-100)",
              color: "#3e3a36",
            }}
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const current = problems[currentIdx];
  const seqSubmitted = submitted[current?.sequence];

  return (
    <div className="max-w-lg mx-auto px-4 py-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => router.push("/s/home")}
          className="p-2 -ml-2 transition-colors duration-300"
          style={{ color: "var(--color-soft-400)" }}
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-sm font-medium" style={{ color: "var(--color-mist-500)" }}>
          第 {currentIdx + 1} / {problems.length} 题
        </span>
        <div className="w-8" />
      </div>

      {/* Progress bar */}
      <div
        className="w-full rounded-full h-2 mb-6"
        style={{ background: "var(--color-mist-200)" }}
      >
        <div
          className="rounded-full h-2 progress-fill transition-all duration-500"
          style={{
            width: `${((currentIdx + 1) / problems.length) * 100}%`,
            background: "var(--color-mist-500)",
          }}
        />
      </div>

      {/* Problem card */}
      {current && (
        <div className="surface-soft rounded-2xl p-8 mb-6 text-center">
          <p className="text-4xl font-semibold tracking-wide" style={{ color: "#3e3a36" }}>
            {current.problem}
          </p>
          {current.hint && (
            <p className="text-sm mt-2" style={{ color: "var(--color-soft-400)" }}>
              {current.hint}
            </p>
          )}
        </div>
      )}

      {seqSubmitted ? (
        <div
          className="rounded-2xl p-6 text-center"
          style={{
            background: results[current.sequence]?.is_correct
              ? "var(--color-mist-50)"
              : "var(--color-blush-50)",
            border: results[current.sequence]?.is_correct
              ? "1px solid rgba(155, 170, 200, 0.15)"
              : "1px solid rgba(242, 168, 171, 0.2)",
          }}
        >
          <p
            className="text-lg font-semibold"
            style={{
              color: results[current.sequence]?.is_correct
                ? "var(--color-mist-500)"
                : "var(--color-blush-400)",
            }}
          >
            {results[current.sequence]?.is_correct ? "✅ 正确！" : "❌ 继续加油"}
          </p>
          <p className="text-sm mt-1" style={{ color: "var(--color-soft-400)" }}>
            等待下一题...
          </p>
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
            disabled={!answer.trim()}
            className="w-full h-14 rounded-2xl text-lg font-semibold flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-30 active:scale-[0.97]"
            style={{ background: "var(--color-mist-500)", color: "white" }}
          >
            <Send className="w-5 h-5" /> 提交
          </button>
        </div>
      )}
    </div>
  );
}
