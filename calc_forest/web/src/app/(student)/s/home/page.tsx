"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, Camera, Download, PenTool, TreePine, ChevronRight, Star } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

interface Dashboard {
  student: { id: string; name: string; grade: number; class_id: string };
  pending_homework: Array<{
    homework_id: string; status: string; assigned_date: string;
    due_date: string; problem_count: number;
  }>;
  growth_summary: { stage: string; days_completed: number; tree_species: string | null };
  weak_areas: Array<{ error_code: string; label: string; accuracy: number }>;
  today_practice: { completed: number; target: number };
}

export default function StudentHomePage() {
  const router = useRouter();
  const [data, setData] = useState<Dashboard | null>(null);
  const [student, setStudent] = useState<{ id: string; name: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("student_session");
    if (!raw) { router.push("/s/login"); return; }
    const session = JSON.parse(raw);
    setStudent(session.student);

    fetch(`${API_BASE}/api/students/${session.student.id}/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [router]);

  const handleDownloadPdf = async (hwId: string) => {
    if (!student) return;
    setDownloading(hwId);
    try {
      const res = await fetch(`${API_BASE}/api/students/${student.id}/homework/${hwId}/pdf`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `作业_${hwId}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch { /* ignore */ }
    setDownloading(null);
  };

  if (!student) return null;

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        <div className="h-8 bg-emerald-100 rounded-lg animate-pulse w-32" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-emerald-50 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-40 bg-emerald-50 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <div className="text-4xl mb-3">🌱</div>
        <p className="text-gray-500 mb-4">加载失败，请检查网络后重试</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm"
        >
          重新加载
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-emerald-800">
            你好，{student.name}！🌳
          </h1>
          <p className="text-emerald-600 text-sm">今天也要加油哦</p>
        </div>
        <button
          onClick={() => { localStorage.removeItem("student_session"); router.push("/s/login"); }}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          退出
        </button>
      </div>

      {data?.today_practice && (
        <div className="bg-white rounded-2xl p-4 shadow-sm flex items-center gap-3">
          <Star className="w-8 h-8 text-amber-500" />
          <div className="flex-1">
            <p className="text-sm text-gray-600">今日练习</p>
            <p className="text-lg font-bold text-emerald-700">
              {data.today_practice.completed} / {data.today_practice.target} 题
            </p>
          </div>
          <button
            onClick={() => router.push("/s/practice")}
            className="h-10 px-4 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
          >
            开始练习
          </button>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold text-emerald-800 mb-3 flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          待做作业
        </h2>
        {data?.pending_homework?.length ? (
          <div className="space-y-2">
            {data.pending_homework.map((hw) => (
              <div
                key={hw.homework_id}
                className="bg-white rounded-xl p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => router.push(`/s/homework/${hw.homework_id}`)}
                    className="flex items-center gap-3 text-left flex-1"
                  >
                    <div>
                      <p className="font-medium text-gray-800">
                        作业 · {hw.problem_count} 题
                      </p>
                      <p className="text-xs text-gray-500">
                        {hw.due_date ? `截止 ${hw.due_date}` : ""}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handleDownloadPdf(hw.homework_id)}
                    disabled={downloading === hw.homework_id}
                    className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100 transition-colors disabled:opacity-50"
                  >
                    <Download className="w-3.5 h-3.5" />
                    {downloading === hw.homework_id ? "下载中..." : "下载作业"}
                  </button>
                  <button
                    onClick={() => router.push(`/s/scan/${hw.homework_id}`)}
                    className="flex items-center gap-1.5 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    扫描上传
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl p-6 text-center text-gray-400">
            暂无待做作业 🎉
          </div>
        )}
      </div>

      {data?.weak_areas?.length ? (
        <div>
          <h2 className="text-lg font-semibold text-emerald-800 mb-3 flex items-center gap-2">
            <PenTool className="w-5 h-5" />
            需要加强
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {data.weak_areas.map((w) => (
              <div key={w.error_code} className="bg-white rounded-xl p-3 text-center shadow-sm">
                <p className="text-xs text-gray-500">{w.error_code}</p>
                <p className="text-sm font-medium text-gray-800 truncate">{w.label}</p>
                <p className="text-xs text-emerald-600">{Math.round(w.accuracy * 100)}%</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {data?.growth_summary && (
        <button
          onClick={() => router.push("/s/growth")}
          className="w-full bg-white rounded-2xl p-4 shadow-sm text-left hover:shadow-md transition-shadow"
        >
          <div className="flex items-center gap-2 mb-2">
            <TreePine className="w-5 h-5 text-emerald-600" />
            <span className="font-medium text-emerald-800">
              成长阶段：{data.growth_summary.stage}
            </span>
            <ChevronRight className="w-4 h-4 text-gray-400 ml-auto" />
          </div>
          <p className="text-sm text-gray-500">
            已坚持 {data.growth_summary.days_completed} 天 · 点击查看详情
          </p>
        </button>
      )}
    </div>
  );
}
