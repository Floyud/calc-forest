"use client";

import { useCallback, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Camera,
  CheckCircle2,
  ChevronLeft,
  Loader2,
  RotateCcw,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { scanAndGradeHomework } from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { ScanGradeResponse, ScanGradeResult } from "@/lib/types";

type Step = "upload" | "processing" | "review" | "done";

const CORRECT_RESULT_LABELS: Record<number, string> = {
  0: "未批",
  1: "正确",
  2: "错误",
  3: "未作答",
};

function OcrSourceBadge({ source }: { source: "baidu" | "local" | null }) {
  if (!source) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium",
        source === "baidu"
          ? "bg-blue-50 text-blue-700 ring-1 ring-blue-200"
          : "bg-gray-100 text-gray-600 ring-1 ring-gray-200",
      )}
    >
      {source === "baidu" ? <Sparkles className="w-3 h-3" /> : null}
      {source === "baidu" ? "百度智能批改" : "本地识别"}
    </span>
  );
}

function ProblemCard({ result }: { result: ScanGradeResult }) {
  const hasBaiduSlots = result.baidu_slots && result.baidu_slots.length > 0;

  const bgColor = result.is_correct
    ? "bg-emerald-50"
    : result.student_answer
      ? "bg-rose-50"
      : "bg-amber-50";

  return (
    <div className={cn("p-3 rounded-xl", bgColor)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800">
            <span className="text-gray-400 mr-1.5">#{result.sequence}</span>
            {result.problem}
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-500 mt-1">
            <span>识别: {result.recognized_text || "—"}</span>
            <span>作答: {result.student_answer || "—"}</span>
            <span>正确答案: {result.correct_answer}</span>
          </div>

          {result.error_code && result.error_label && (
            <div className="mt-1.5 inline-flex items-center gap-1.5 bg-white/80 px-2 py-0.5 rounded-lg">
              <span className="text-xs font-mono text-rose-600">{result.error_code}</span>
              <span className="text-xs text-gray-500">{result.error_label}</span>
            </div>
          )}

          {hasBaiduSlots && (
            <div className="mt-1.5 space-y-0.5">
              {result.baidu_slots!.map((slot) => (
                <div key={slot.slot_id} className="text-xs text-gray-500 flex items-center gap-1.5">
                  <span
                    className={cn(
                      "w-1.5 h-1.5 rounded-full shrink-0",
                      slot.correct_result === 1
                        ? "bg-emerald-400"
                        : slot.correct_result === 2
                          ? "bg-rose-400"
                          : "bg-gray-300",
                    )}
                  />
                  <span>
                    {CORRECT_RESULT_LABELS[slot.correct_result] ?? "未知"}
                  </span>
                  {slot.reason && (
                    <span className="text-gray-400">— {slot.reason}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="shrink-0 mt-0.5">
          {result.is_correct ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          ) : (
            <X className="w-5 h-5 text-rose-500" />
          )}
        </div>
      </div>
    </div>
  );
}

export default function ScanUploadPage() {
  const router = useRouter();
  const params = useParams();
  const hwId = params.hwId as string;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>("upload");
  const [preview, setPreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [gradeData, setGradeData] = useState<ScanGradeResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const student =
    typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("student_session") || "{}")?.student
      : null;

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return;
    setErrorMsg(null);
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handleCapture = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleSubmit = useCallback(async () => {
    if (!imageFile || !student) return;
    setStep("processing");
    setErrorMsg(null);

    try {
      const data = await scanAndGradeHomework(hwId, student.id, imageFile);
      setGradeData(data);
      if (data.status === "no_ocr_results") {
        setErrorMsg("未能识别到答案，请重新拍照并确保字迹清晰");
        setStep("upload");
      } else {
        setStep("review");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.displayMessage);
      } else {
        setErrorMsg("上传失败，请重试");
      }
      setStep("upload");
    }
  }, [imageFile, student, hwId]);

  const handleRetryBaidu = useCallback(() => {
    setPreview(null);
    setImageFile(null);
    setGradeData(null);
    setErrorMsg(null);
    setStep("upload");
  }, []);

  const handleConfirm = useCallback(() => {
    setStep("done");
  }, []);

  if (!student) {
    router.push("/s/login");
    return null;
  }

  const wrongCount = gradeData
    ? gradeData.grading_summary.total - gradeData.grading_summary.correct
    : 0;
  const unrecognizedCount = gradeData
    ? gradeData.total_problems - gradeData.recognized_count
    : 0;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/s/home")}
          className="p-2 -ml-2 rounded-lg hover:bg-white/60"
        >
          <ChevronLeft className="w-5 h-5 text-emerald-700" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-emerald-800">扫描上传</h1>
          <p className="text-xs text-gray-500">作业 {hwId}</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex gap-2">
        {(["upload", "processing", "review", "done"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div
              className={cn(
                "h-2 rounded-full flex-1 transition-colors",
                i <= ["upload", "processing", "review", "done"].indexOf(step)
                  ? "bg-emerald-500"
                  : "bg-gray-200",
              )}
            />
          </div>
        ))}
      </div>

      {/* Error message */}
      {errorMsg && step === "upload" && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3 rounded-xl">
          {errorMsg}
        </div>
      )}

      {/* Upload step */}
      {step === "upload" && (
        <div className="space-y-4">
          {!preview ? (
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="bg-white rounded-2xl p-8 shadow-sm text-center border-2 border-dashed border-emerald-300 hover:border-emerald-400 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <Camera className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
              <p className="text-emerald-700 font-medium">拍照或上传作业</p>
              <p className="text-sm text-gray-400 mt-1">
                支持拍照、相册选取、拖拽上传
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleCapture}
                className="hidden"
              />
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-4 shadow-sm">
              <div className="relative">
                <img
                  src={preview}
                  alt="作业预览"
                  className="w-full rounded-xl"
                />
                <button
                  onClick={() => {
                    setPreview(null);
                    setImageFile(null);
                  }}
                  className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="flex gap-3 mt-4">
                <button
                  onClick={() => {
                    setPreview(null);
                    setImageFile(null);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200"
                >
                  <RotateCcw className="w-4 h-4" />
                  重拍
                </button>
                <button
                  onClick={handleSubmit}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700"
                >
                  <Upload className="w-4 h-4" />
                  提交批改
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Processing step */}
      {step === "processing" && (
        <div className="bg-white rounded-2xl p-12 shadow-sm text-center">
          <Loader2 className="w-12 h-12 text-emerald-600 mx-auto animate-spin" />
          <p className="text-emerald-700 font-medium mt-4">正在识别和批改...</p>
          <p className="text-sm text-gray-400 mt-1">请稍候，AI 正在分析你的作业</p>
        </div>
      )}

      {/* Review step */}
      {step === "review" && gradeData && (
        <div className="space-y-4">
          {/* Summary card */}
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-sm text-gray-500">
              识别了 {gradeData.recognized_count} / {gradeData.total_problems}{" "}
              题的答案
            </p>
            <div className="flex justify-center gap-6 mt-3">
              <div>
                <p className="text-2xl font-bold text-emerald-600">
                  {gradeData.grading_summary.correct}
                </p>
                <p className="text-xs text-gray-400">正确</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-rose-600">{wrongCount}</p>
                <p className="text-xs text-gray-400">错误</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-600">
                  {Math.round(gradeData.grading_summary.accuracy * 100)}%
                </p>
                <p className="text-xs text-gray-400">正确率</p>
              </div>
              {unrecognizedCount > 0 && (
                <div>
                  <p className="text-2xl font-bold text-amber-600">
                    {unrecognizedCount}
                  </p>
                  <p className="text-xs text-gray-400">未识别</p>
                </div>
              )}
            </div>
            <div className="mt-3">
              <OcrSourceBadge source={gradeData.ocr_source} />
            </div>
          </div>

          {/* Per-problem results */}
          <div className="bg-white rounded-2xl p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-emerald-800 mb-3">
              逐题结果
            </h3>
            <div className="space-y-2">
              {gradeData.results.map((r) => (
                <ProblemCard key={r.sequence} result={r} />
              ))}
            </div>
          </div>

          {/* Retry with Baidu button */}
          {gradeData.ocr_source === "local" &&
            (gradeData.status === "partial" || wrongCount > 0) && (
              <button
                onClick={handleRetryBaidu}
                className="w-full py-3 bg-blue-50 text-blue-700 rounded-xl text-sm font-medium hover:bg-blue-100 flex items-center justify-center gap-2 ring-1 ring-blue-200"
              >
                <Sparkles className="w-4 h-4" />
                用百度智能批改重试
              </button>
            )}

          <button
            onClick={handleConfirm}
            className="w-full py-3 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700"
          >
            确认结果
          </button>
        </div>
      )}

      {/* Done step */}
      {step === "done" && (
        <div className="bg-white rounded-2xl p-8 shadow-sm text-center">
          <CheckCircle2 className="w-16 h-16 text-emerald-600 mx-auto" />
          <h2 className="text-lg font-bold text-emerald-800 mt-4">
            批改完成！
          </h2>
          <p className="text-sm text-gray-500 mt-2">
            作业已提交，等待老师审核确认
          </p>
          <button
            onClick={() => router.push("/s/home")}
            className="mt-6 px-6 py-3 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700"
          >
            返回首页
          </button>
        </div>
      )}
    </div>
  );
}
