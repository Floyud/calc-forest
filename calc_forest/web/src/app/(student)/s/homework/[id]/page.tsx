"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Camera, Check, ChevronRight, ChevronLeft, Send, X, RotateCcw } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

interface Problem {
  sequence: number;
  problem: string;
  difficulty: string;
  knowledge_point: string;
}

interface OCRResult {
  text: string;
  confidence: number;
}

const FALLBACK_GRADE6_PROBLEMS: Problem[] = [
  { sequence: 1, problem: "(3/4-2/5)÷7/10=", difficulty: "C", knowledge_point: "分数四则混合" },
  { sequence: 2, problem: "36÷(3/5)×25%=", difficulty: "C", knowledge_point: "百分数综合计算" },
  { sequence: 3, problem: "甲:乙=5:8，乙比甲多18，甲是多少？", difficulty: "C", knowledge_point: "比的应用" },
  { sequence: 4, problem: "圆形花坛半径4.5米，周长是多少米？", difficulty: "B", knowledge_point: "圆的周长" },
];

export default function HomeworkDoPage() {
  const router = useRouter();
  const params = useParams();
  const homeworkId = params.id as string;
  const [studentId, setStudentId] = useState("");
  const [problems, setProblems] = useState<Problem[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<Array<{ is_correct: boolean; error_code?: string }> | null>(null);

  const [cameraOpen, setCameraOpen] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("student_session");
    if (!raw) { router.push("/s/login"); return; }
    const session = JSON.parse(raw);
    setStudentId(session.student.id);

    fetch(`${API_BASE}/api/students/${session.student.id}/homework/${homeworkId}/problems`)
      .then((r) => r.json())
      .then((data) => {
        setProblems(Array.isArray(data) && data.length > 0 ? data : FALLBACK_GRADE6_PROBLEMS);
        setLoading(false);
      })
      .catch(() => {
        setProblems(FALLBACK_GRADE6_PROBLEMS);
        setLoading(false);
      });
  }, [homeworkId, router]);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      setCameraOpen(true);
      setOcrResult(null);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      }, 100);
    } catch {
      alert("无法访问摄像头，请检查权限");
    }
  }, []);

  const captureAndRecognize = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);

    setOcrLoading(true);
    try {
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const formData = new FormData();
        formData.append("file", blob, "capture.jpg");
        const res = await fetch(`${API_BASE}/api/ocr/recognize`, { method: "POST", body: formData });
        const data = await res.json();
        setOcrResult({ text: data.text, confidence: data.confidence });

        if (blob) {
          const uploadForm = new FormData();
          uploadForm.append("file", blob, "capture.jpg");
          uploadForm.append("student_id", studentId);
          uploadForm.append("homework_id", homeworkId);
          fetch(`${API_BASE}/api/ocr/upload`, { method: "POST", body: uploadForm }).catch(() => {});
        }
      }, "image/jpeg", 0.9);
    } finally {
      setOcrLoading(false);
    }
  }, [studentId, homeworkId]);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOpen(false);
  }, []);

  const confirmOcr = useCallback(() => {
    if (ocrResult?.text && problems.length > 0) {
      setAnswers((prev) => ({ ...prev, [problems[currentIdx].sequence]: ocrResult.text }));
    }
    stopCamera();
    setOcrResult(null);
  }, [ocrResult, currentIdx, problems, stopCamera]);

  const submitHomework = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/homework/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          homework_id: homeworkId,
          student_id: studentId,
          answers: Object.entries(answers).map(([seq, ans]) => ({
            problem_sequence: parseInt(seq),
            raw_answer: ans,
          })),
        }),
      });
      const data = await res.json();
      if (data.grading_results) {
        setResults(data.grading_results);
      }
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin w-8 h-8 border-3 border-emerald-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (submitted) {
    const correct = results?.filter((r) => r.is_correct).length ?? 0;
    const total = results?.length ?? problems.length;
    return (
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl p-6 shadow-lg text-center">
          <div className="text-5xl mb-4">{correct === total ? "🎉" : correct > total / 2 ? "👍" : "💪"}</div>
          <h2 className="text-2xl font-bold text-emerald-800 mb-2">
            {correct}/{total} 题正确
          </h2>
          <p className="text-gray-500 mb-6">
            正确率 {Math.round((correct / total) * 100)}%
          </p>
          {results && (
            <div className="space-y-2 mb-6 text-left">
              {results.map((r, i) => (
                <div key={i} className={`p-3 rounded-lg ${r.is_correct ? "bg-emerald-50" : "bg-red-50"}`}>
                  <span className={r.is_correct ? "text-emerald-600" : "text-red-600"}>
                    {r.is_correct ? "✓" : "✗"} 第 {i + 1} 题
                  </span>
                  {!r.is_correct && r.error_code && (
                    <span className="text-xs text-gray-500 ml-2">({r.error_code})</span>
                  )}
                </div>
              ))}
            </div>
          )}
          <button onClick={() => router.push("/s/home")} className="h-12 px-8 bg-emerald-600 text-white rounded-xl font-medium">
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const current = problems[currentIdx];
  if (!current) {
    return (
      <div className="max-w-lg mx-auto px-4 py-6 text-center text-gray-500">
        没有找到题目
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-4">
      <div className="flex items-center justify-between mb-4">
        <button onClick={() => router.push("/s/home")} className="p-2 -ml-2 text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-sm font-medium text-emerald-700">
          {currentIdx + 1} / {problems.length}
        </span>
        <div className="w-8" />
      </div>

      <div className="w-full bg-emerald-100 rounded-full h-2 mb-6">
        <div
          className="bg-emerald-500 rounded-full h-2 transition-all"
          style={{ width: `${((currentIdx + 1) / problems.length) * 100}%` }}
        />
      </div>

      <div className="bg-white rounded-2xl p-7 shadow-sm mb-6 text-center border border-emerald-100">
        <div className="mb-4 flex items-center justify-center gap-2">
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            {current.knowledge_point || "六年级综合计算"}
          </span>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
            current.difficulty === "C" ? "bg-rose-50 text-rose-600" : "bg-amber-50 text-amber-700"
          }`}>
            {current.difficulty === "C" ? "挑战题" : "提升题"}
          </span>
        </div>
        <p className="text-3xl font-bold leading-tight text-gray-800 tracking-wide">
          {current.problem}
        </p>
      </div>

      <div className="bg-white rounded-2xl p-4 shadow-sm mb-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm font-medium text-gray-600">我的答案</span>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            inputMode="numeric"
            value={answers[current.sequence] || ""}
            onChange={(e) => setAnswers((prev) => ({ ...prev, [current.sequence]: e.target.value }))}
            placeholder="输入答案..."
            className="flex-1 h-14 text-2xl text-center border-2 border-emerald-200 rounded-xl focus:border-emerald-500 focus:outline-none font-mono"
          />
          <button
            onClick={startCamera}
            className="h-14 w-14 flex items-center justify-center bg-emerald-100 hover:bg-emerald-200 rounded-xl transition-colors"
          >
            <Camera className="w-6 h-6 text-emerald-700" />
          </button>
        </div>
        {answers[current.sequence] && (
          <button
            onClick={() => setAnswers((prev) => {
              const next = { ...prev };
              delete next[current.sequence];
              return next;
            })}
            className="mt-2 text-xs text-gray-400 flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" /> 清除答案
          </button>
        )}
      </div>

      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
          disabled={currentIdx === 0}
          className="h-12 px-5 bg-gray-100 text-gray-600 rounded-xl font-medium disabled:opacity-30 flex items-center gap-1"
        >
          <ChevronLeft className="w-4 h-4" /> 上一题
        </button>
        {currentIdx === problems.length - 1 ? (
          <button
            onClick={submitHomework}
            disabled={submitting || Object.keys(answers).length < problems.length}
            className="h-12 px-6 bg-emerald-600 text-white rounded-xl font-semibold disabled:opacity-30 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            {submitting ? "提交中..." : "提交作业"}
          </button>
        ) : (
          <button
            onClick={() => setCurrentIdx((i) => i + 1)}
            className="h-12 px-5 bg-emerald-600 text-white rounded-xl font-medium flex items-center gap-1"
          >
            下一题 <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="mt-4 flex justify-center gap-1 flex-wrap">
        {problems.map((p, i) => (
          <button
            key={p.sequence}
            onClick={() => setCurrentIdx(i)}
            className={`w-8 h-8 rounded-lg text-xs font-medium flex items-center justify-center transition-colors ${
              i === currentIdx
                ? "bg-emerald-600 text-white"
                : answers[p.sequence]
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-gray-100 text-gray-400"
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>

      {cameraOpen && (
        <div className="fixed inset-0 bg-black/80 z-50 flex flex-col">
          <div className="flex-1 relative">
            <video ref={videoRef} playsInline autoPlay muted className="w-full h-full object-contain" />
            <canvas ref={canvasRef} className="hidden" />
            <button
              onClick={stopCamera}
              className="absolute top-4 right-4 w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"
            >
              <X className="w-6 h-6 text-white" />
            </button>
          </div>

          <div className="bg-black p-4">
            {ocrLoading ? (
              <div className="text-white text-center py-4">
                <div className="animate-spin w-6 h-6 border-2 border-white border-t-transparent rounded-full mx-auto mb-2" />
                识别中...
              </div>
            ) : ocrResult ? (
              <div className="space-y-3">
                <div className="bg-white/10 rounded-xl p-4">
                  <p className="text-white/60 text-xs mb-1">识别结果（置信度 {Math.round(ocrResult.confidence * 100)}%）</p>
                  <p className="text-white text-2xl font-mono text-center">{ocrResult.text || "（未识别到内容）"}</p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => { setOcrResult(null); }}
                    className="flex-1 h-12 bg-white/10 text-white rounded-xl font-medium"
                  >
                    重新拍照
                  </button>
                  <button
                    onClick={confirmOcr}
                    disabled={!ocrResult.text}
                    className="flex-1 h-12 bg-emerald-600 text-white rounded-xl font-semibold disabled:opacity-30 flex items-center justify-center gap-2"
                  >
                    <Check className="w-5 h-5" /> 确认
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <button
                  onClick={captureAndRecognize}
                  className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-lg"
                >
                  <div className="w-14 h-14 border-4 border-gray-300 rounded-full" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
