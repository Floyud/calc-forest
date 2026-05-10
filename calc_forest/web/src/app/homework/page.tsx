"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Archive,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Download,
  Eye,
  FileText,
  FileSearch,
  Loader2,
  RefreshCw,
  ScanSearch,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type {
  HomeworkDetail,
  HomeworkGenerateRequest,
  HomeworkPdfRecord,
  OCRTaskResponse,
  SimulatedRecognitionAnswer,
} from "@/lib/types";
import {
  assignHomework,
  generateHomework,
  getClassHomeworkPdfs,
  getHomeworkDetail,
  getHomeworkSubmissions,
  getPdfUrl,
  getRecognitionTask,
  uploadHomeworkRecognition,
} from "@/lib/api";
import { getStatusLabel, getReviewLabel, getErrorCodeDisplay } from "@/lib/labels";

const DEFAULT_FORM: HomeworkGenerateRequest = {
  class_id: "G6C1",
  student_id: "S001",
  grade: 6,
  error_codes_target: ["E03", "E02"],
  problem_count: 4,
  difficulty: "A",
};

function statusTone(status: string) {
  if (status === "archived" || status === "graded" || status === "recognized") return "bg-emerald-100 text-emerald-700";
  if (status === "processing" || status === "queued" || status === "submitted" || status === "in_progress") {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-forest-100 text-forest-700";
}

function studentLabel(sid: string | null): string {
  if (!sid) return "班级共用";
  return sid;
}

export default function HomeworkPage() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [homework, setHomework] = useState<HomeworkDetail | null>(null);
  const [studentAnswers, setStudentAnswers] = useState<Record<number, string>>({});
  const [scanTask, setScanTask] = useState<OCRTaskResponse | null>(null);
  const [submissions, setSubmissions] = useState<OCRTaskResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [pdfs, setPdfs] = useState<HomeworkPdfRecord[]>([]);
  const [pdfsLoading, setPdfsLoading] = useState(false);
  const [pdfsError, setPdfsError] = useState<string | null>(null);

  const recognizedDone = scanTask?.archive_status === "archived";

  const loadPdfs = useCallback(async () => {
    setPdfsLoading(true);
    setPdfsError(null);
    try {
      const data = await getClassHomeworkPdfs("G6C1");
      setPdfs(data);
    } catch (err) {
      setPdfsError(err instanceof Error ? err.message : "加载 PDF 列表失败");
    } finally {
      setPdfsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPdfs();
  }, [loadPdfs]);

  useEffect(() => {
    if (!scanTask || recognizedDone) return;

    const timer = window.setTimeout(async () => {
      try {
        const next = await getRecognitionTask(scanTask.scan_id);
        setScanTask(next);
        if (homework) {
          const latest = await getHomeworkSubmissions(homework.id);
          setSubmissions(latest);
        }
      } catch {
      }
    }, 1200);

    return () => window.clearTimeout(timer);
  }, [scanTask, recognizedDone, homework]);

  const completionSummary = useMemo(() => {
    if (!scanTask?.diagnosis) return null;
    return `${scanTask.diagnosis.correct_count}/${scanTask.diagnosis.total_problems} 正确，准确率 ${Math.round(scanTask.diagnosis.accuracy * 100)}%`;
  }, [scanTask]);

  const pdfsByHomework = useMemo(() => {
    const groups: Record<string, HomeworkPdfRecord[]> = {};
    for (const pdf of pdfs) {
      const key = pdf.homework_id;
      if (!groups[key]) groups[key] = [];
      groups[key].push(pdf);
    }
    return Object.entries(groups).sort(
      ([, a], [, b]) => (b[0]?.hw_created ?? "").localeCompare(a[0]?.hw_created ?? ""),
    );
  }, [pdfs]);

  async function handleGenerate() {
    setError(null);

    if (!form.error_codes_target || form.error_codes_target.length === 0) {
      setError("请至少选择一个错因类型");
      return;
    }
    if (!form.problem_count || form.problem_count < 1 || form.problem_count > 20) {
      setError("题目数量需在1-20之间");
      return;
    }

    setLoading(true);
    setError(null);
    setHomework(null);
    setScanTask(null);
    setSubmissions([]);

    try {
      const generated = await generateHomework(form);
      const detail = await getHomeworkDetail(generated.homework_id);
      setHomework(detail);
      setStudentAnswers(
        Object.fromEntries(detail.problems.map((problem) => [problem.sequence, ""])),
      );
      const existing = await getHomeworkSubmissions(detail.id);
      setSubmissions(existing);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成作业失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleAssign() {
    if (!homework) return;
    setAssigning(true);
    setError(null);
    try {
      await assignHomework(homework.id);
      const detail = await getHomeworkDetail(homework.id);
      setHomework(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "布置作业失败");
    } finally {
      setAssigning(false);
    }
  }

  async function handleSimulateUpload() {
    if (!homework) return;
    setUploading(true);
    setError(null);
    try {
      const answers: SimulatedRecognitionAnswer[] = homework.problems.map((problem) => ({
        problem_sequence: problem.sequence,
        raw_answer: studentAnswers[problem.sequence] ?? "",
      }));
      const task = await uploadHomeworkRecognition({
        homework_id: homework.id,
        student_id: form.student_id ?? "S001",
        answers,
        source_label: "blank_area_simulation",
      });
      setScanTask(task);
      const latest = await getHomeworkSubmissions(homework.id);
      setSubmissions(latest);
    } catch (err) {
      setError(err instanceof Error ? err.message : "模拟上传失败");
    } finally {
      setUploading(false);
    }
  }

  function openPdf(pdfId: string) {
    window.open(getPdfUrl(pdfId), "_blank");
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-foreground">个性化作业闭环</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            生成个性化作业，布置给学生，模拟作答后自动判题。所有结果需教师审核。
          </p>
        </div>
        <Badge className="w-fit bg-forest-100 text-forest-700">
          模拟多模态识别 + 教师审核
        </Badge>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-forest-600" />
              作业生成入口
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              当前仍由教师发起，后续可接入智能生成入口。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="classId">班级 ID</Label>
                <Input
                  id="classId"
                  value={form.class_id}
                  onChange={(e) => setForm((prev) => ({ ...prev, class_id: e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="studentId">学生 ID</Label>
                <Input
                  id="studentId"
                  value={form.student_id ?? ""}
                  onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="grade">年级</Label>
                <Input
                  id="grade"
                  type="number"
                  min={1}
                  max={6}
                  value={form.grade}
                  onChange={(e) => setForm((prev) => ({ ...prev, grade: Number(e.target.value) }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="problemCount">题量</Label>
                <Input
                  id="problemCount"
                  type="number"
                  min={1}
                  max={20}
                  value={form.problem_count ?? 4}
                  onChange={(e) => setForm((prev) => ({ ...prev, problem_count: Number(e.target.value) }))}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="errorCodes">目标错因</Label>
              <Input
                id="errorCodes"
                value={(form.error_codes_target ?? []).join(",")}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    error_codes_target: e.target.value
                      .split(",")
                      .map((item) => item.trim())
                      .filter(Boolean),
                  }))
                }
                placeholder="E03,E02"
              />
            </div>

            <Button onClick={handleGenerate} disabled={loading} className="bg-orange-500 text-white hover:bg-orange-400">
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
              生成个性化作业草案
            </Button>

            {error && <p className="text-sm text-rose-500">{error}</p>}

            {homework && (
              <>
                <Separator className="bg-forest-200" />
                <div className="rounded-lg border border-forest-200 bg-forest-50/50 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className={statusTone(homework.status)}>{getStatusLabel(homework.status)}</Badge>
                    <Badge variant="outline" className="border-forest-300 text-muted-foreground">
                      HW {homework.id}
                    </Badge>
                  </div>
                  <p className="mt-3 text-sm text-foreground">
                    错因目标：{homework.error_codes_target.join(", ") || "自动推断"}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    知识点：{homework.knowledge_points.join(" / ") || "待推断"}
                  </p>
                  <Button
                    onClick={handleAssign}
                    disabled={assigning || homework.status === "assigned" || homework.status === "in_progress"}
                    variant="outline"
                    className="mt-4 border-forest-300 text-foreground hover:bg-forest-50"
                  >
                    {assigning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ClipboardCheck className="mr-2 h-4 w-4" />}
                    {homework.status === "assigned" || homework.status === "in_progress" ? "已布置" : "布置作业"}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-warm-400" />
                学生作答预览与模拟上传
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                不做完整学生 App，只提供受控演示面，让教师看到提交后如何进入识别与归档。
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!homework ? (
                <p className="text-sm text-muted-foreground">先在左侧生成作业草案。</p>
              ) : (
                <>
                  {homework.problems.map((problem) => (
                    <div key={problem.id} className="rounded-lg border border-forest-200 bg-forest-50/30 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">第 {problem.sequence} 题</p>
                          <p className="mt-1 text-base text-foreground">{problem.problem}</p>
                        </div>
                        <Badge variant="outline" className="border-forest-300 text-muted-foreground">
                           {getErrorCodeDisplay(problem.target_error_code)}
                         </Badge>
                      </div>
                      <Textarea
                        className="mt-3 min-h-20"
                        placeholder="模拟学生写在空白处的答案或简短过程"
                        value={studentAnswers[problem.sequence] ?? ""}
                        onChange={(e) =>
                          setStudentAnswers((prev) => ({
                            ...prev,
                            [problem.sequence]: e.target.value,
                          }))
                        }
                      />
                    </div>
                  ))}

                  <Button
                    onClick={handleSimulateUpload}
                    disabled={uploading || homework.status === "draft"}
                    className="bg-forest-600 text-white hover:bg-forest-500"
                  >
                    {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ScanSearch className="mr-2 h-4 w-4" />}
                    模拟多模态上传
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSearch className="h-4 w-4 text-warm-400" />
                识别、判题与归档状态
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                状态流程：草稿 → 已识别 → 已批改 → 已归档
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!scanTask ? (
                <p className="text-sm text-muted-foreground">上传后这里会开始滚动显示识别与归档状态。</p>
              ) : (
                <>
                  <div className="grid gap-3 md:grid-cols-4">
                    <div className="rounded-lg border border-forest-200 bg-forest-50/30 p-3">
                      <p className="text-xs text-muted-foreground">识别</p>
                      <Badge className={`mt-2 ${statusTone(scanTask.recognition_status)}`}>{getStatusLabel(scanTask.recognition_status)}</Badge>
                    </div>
                    <div className="rounded-lg border border-forest-200 bg-forest-50/30 p-3">
                      <p className="text-xs text-muted-foreground">批改</p>
                      <Badge className={`mt-2 ${statusTone(scanTask.grading_status)}`}>{getStatusLabel(scanTask.grading_status)}</Badge>
                    </div>
                    <div className="rounded-lg border border-forest-200 bg-forest-50/30 p-3">
                      <p className="text-xs text-muted-foreground">归档</p>
                      <Badge className={`mt-2 ${statusTone(scanTask.archive_status)}`}>{getStatusLabel(scanTask.archive_status)}</Badge>
                    </div>
                    <div className="rounded-lg border border-forest-200 bg-forest-50/30 p-3">
                      <p className="text-xs text-muted-foreground">审核</p>
                      <Badge className="mt-2 bg-sky-100 text-sky-700">{getReviewLabel(scanTask.review_status)}</Badge>
                    </div>
                  </div>

                  <div className="rounded-lg border border-forest-200 bg-forest-50/30 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">识别结果</p>
                    <div className="mt-3 space-y-2">
                      {scanTask.recognized_answers.length === 0 ? (
                        <p className="text-sm text-muted-foreground">还在识别中，下一轮轮询会产出结构化识别结果。</p>
                      ) : (
                        scanTask.recognized_answers.map((item) => (
                          <div key={item.problem_sequence} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-forest-200 bg-white px-3 py-2 text-sm">
                            <span className="text-foreground">第 {item.problem_sequence} 题</span>
                            <span className="text-muted-foreground">原始: {item.raw_answer || "∅"}</span>
                            <span className="text-foreground">识别: {item.recognized_answer || "∅"}</span>
                            <span className="text-emerald-600">{Math.round(item.confidence * 100)}%</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {scanTask.diagnosis && (
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                      <div className="flex items-center gap-2 text-emerald-700">
                        <CheckCircle2 className="h-4 w-4" />
                        <span className="font-medium">规则判题与归档摘要</span>
                      </div>
                      <p className="mt-3 text-sm text-foreground">{completionSummary}</p>
                      <p className="mt-2 text-sm text-muted-foreground">
                        主错因：{scanTask.diagnosis.primary_errors.join(", ") || "无"}
                      </p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        建议：{scanTask.diagnosis.next_suggestion ?? "待教师进一步处理"}
                      </p>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Archive className="h-4 w-4 text-forest-600" />
                提交归档列表
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {submissions.length === 0 ? (
                <p className="text-sm text-muted-foreground">当前作业还没有归档记录。</p>
              ) : (
                submissions.map((item) => (
                  <div key={item.scan_id} className="rounded-lg border border-forest-200 bg-forest-50/30 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm text-foreground">扫描 {item.scan_id}</p>
                        <p className="text-xs text-muted-foreground">{item.uploaded_at}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                         <Badge className={statusTone(item.recognition_status)}>{getStatusLabel(item.recognition_status)}</Badge>
                         <Badge className={statusTone(item.grading_status)}>{getStatusLabel(item.grading_status)}</Badge>
                         <Badge className={statusTone(item.archive_status)}>{getStatusLabel(item.archive_status)}</Badge>
                       </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Separator className="my-10 bg-forest-200" />

      <section>
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
              <FileText className="h-5 w-5 text-forest-600" />
              作业 PDF 管理
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              查看和下载已生成的个性化作业 PDF 文件。
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadPdfs}
            disabled={pdfsLoading}
            className="w-fit border-forest-300 text-foreground hover:bg-forest-50"
          >
            {pdfsLoading
              ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              : <RefreshCw className="mr-1.5 h-3.5 w-3.5" />}
            刷新列表
          </Button>
        </div>

        {pdfsError && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
            {pdfsError}
          </div>
        )}

        {pdfs.length === 0 && !pdfsLoading && (
          <Card className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardContent className="py-12 text-center">
              <FileText className="mx-auto h-10 w-10 text-forest-300" />
              <p className="mt-3 text-sm text-muted-foreground">
                暂无已生成的 PDF 文件。请先通过批量生成接口创建作业。
              </p>
            </CardContent>
          </Card>
        )}

        {pdfsByHomework.map(([hwId, hwPdfs]) => (
          <Card key={hwId} className="mb-5 border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-base">
                  作业 {hwId}
                </CardTitle>
                <Badge className={statusTone(hwPdfs[0].hw_status)}>
                   {getStatusLabel(hwPdfs[0].hw_status)}
                 </Badge>
                <Badge variant="outline" className="border-forest-300 text-xs text-muted-foreground">
                  {hwPdfs[0].hw_created}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  共 {hwPdfs.length} 份
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {hwPdfs.map((pdf) => (
                  <div
                    key={pdf.id}
                    className="group rounded-lg border border-forest-200 bg-gradient-to-br from-forest-50/60 to-white p-4 transition-shadow hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <FileText className="h-4 w-4 shrink-0 text-forest-500" />
                          <p className="truncate text-sm font-medium text-foreground">
                            {studentLabel(pdf.student_id)}
                          </p>
                        </div>
                        <p className="mt-1.5 text-xs text-muted-foreground">
                          {pdf.generated_at}
                        </p>
                        <Badge
                          variant="outline"
                          className="mt-2 border-forest-200 text-[10px] text-muted-foreground"
                        >
                          {pdf.pdf_type === "class" ? "班级共用" : "个人定制"}
                        </Badge>
                      </div>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-forest-300 text-foreground hover:bg-forest-50"
                        onClick={() => openPdf(pdf.id)}
                      >
                        <Eye className="mr-1 h-3 w-3" />
                        查看
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        aria-label="下载PDF"
                        className="border-forest-300 text-foreground hover:bg-forest-50"
                        onClick={() => {
                          const a = document.createElement("a");
                          a.href = getPdfUrl(pdf.id);
                          a.download = `homework_${pdf.student_id ?? "class"}.pdf`;
                          a.click();
                        }}
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
