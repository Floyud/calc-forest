"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TreePine, LogIn } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export default function StudentLoginPage() {
  const router = useRouter();
  const [studentId, setStudentId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!studentId.trim()) {
      setError("请输入学号");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/student-auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId.trim() }),
      });
      if (!res.ok) {
        setError("学号不存在，请检查");
        return;
      }
      const data = await res.json();
      localStorage.setItem("student_session", JSON.stringify(data));
      router.push("/s/home");
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm px-6">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
          style={{
            background: "linear-gradient(135deg, var(--color-mist-300) 0%, var(--color-mist-400) 100%)",
            boxShadow: "0 8px 24px rgba(148, 168, 200, 0.25)"
          }}>
          <TreePine className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-2xl font-semibold" style={{ color: "#3e3a36", lineHeight: 1.4 }}>
          我的计算森林
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--color-soft-500)" }}>
          输入学号开始学习
        </p>
      </div>

      <div className="surface-glass rounded-2xl p-6 space-y-4"
        style={{ boxShadow: "0 12px 40px rgba(120, 115, 100, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6)" }}>
        <div>
          <label className="block text-sm font-medium mb-1.5"
            style={{ color: "var(--color-soft-500)" }}>学号</label>
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            placeholder="例如 S001"
            className="w-full h-14 px-4 text-lg rounded-xl text-center transition-all duration-300"
            style={{
              border: "1px solid rgba(180, 172, 158, 0.2)",
              background: "rgba(255, 255, 255, 0.6)",
              color: "#3e3a36",
            }}
            autoFocus
          />
        </div>

        {error && (
          <p className="text-sm text-center" style={{ color: "var(--color-blush-400)" }}>{error}</p>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full h-14 rounded-xl text-lg font-semibold flex items-center justify-center gap-2 transition-all duration-300"
          style={{
            background: loading
              ? "var(--color-mist-200)"
              : "linear-gradient(135deg, var(--color-mist-400) 0%, var(--color-mist-500) 100%)",
            color: "white",
            boxShadow: loading
              ? "none"
              : "0 4px 16px rgba(148, 168, 200, 0.3)",
            transform: "translateY(0)",
          }}
          onMouseEnter={(e) => { if (!loading) e.currentTarget.style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}
        >
          <LogIn className="w-5 h-5" />
          {loading ? "登录中..." : "进入我的森林"}
        </button>
      </div>

      <p className="text-center text-xs mt-6" style={{ color: "var(--color-soft-400)" }}>
        提示：演示可用学号 S001 - S050
      </p>
    </div>
  );
}
