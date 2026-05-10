"use client";

import { useState, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  X, TrendingUp, TrendingDown, Minus, BarChart3, Target, User,
  Loader2, Check, Pencil, BookOpen, Lightbulb, AlertTriangle,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateStudentProfile } from "@/lib/api/hooks";
import { getStudentProfile } from "@/lib/api";
import { API_BASE } from "@/lib/config";
import { SvgTree } from "./trees/SvgTree";
import { getTreeColors } from "./trees/treeColors";
import { getEmotionLabel, getEmotionEmoji } from "./trees/useEmotionState";
import type { StudentTree, WeakKnowledgePoint } from "@/lib/types";
import { ERROR_LABELS, GROWTH_STAGES } from "@/lib/types";

const AccuracyTrendChart = dynamic(
  () => import("./AccuracyTrendChart").then((m) => ({ default: m.AccuracyTrendChart })),
  { ssr: false },
);

const ErrorRadarChart = dynamic(
  () => import("./ErrorRadarChart").then((m) => ({ default: m.ErrorRadarChart })),
  { ssr: false },
);

function getStageLabel(stage: string): string {
  const found = GROWTH_STAGES.find((s) => s.key === stage);
  return found ? found.label : "播种";
}

function TrendIcon({ current, previous }: { current: number; previous: number }) {
  const diff = current - previous;
  if (diff > 0.05) return <TrendingUp className="h-4 w-4 text-forest-600" />;
  if (diff < -0.05) return <TrendingDown className="h-4 w-4 text-volcano-400" />;
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

const GRADE_LABELS: Record<number, string> = {
  1: "一年级", 2: "二年级", 3: "三年级",
  4: "四年级", 5: "五年级", 6: "六年级",
};

function getGradeLabel(grade: number): string {
  return GRADE_LABELS[grade] ?? `${grade}年级`;
}

function accuracyBadgeColor(acc: number): string {
  if (acc >= 0.8) return "bg-forest-100 text-forest-700 border-forest-200";
  if (acc >= 0.6) return "bg-warm-100 text-warm-700 border-warm-200";
  return "bg-volcano-100 text-volcano-500 border-volcano-200";
}

function WeakKnowledgeCard({ point }: { point: WeakKnowledgePoint }) {
  const borderColor =
    point.mastery_zone === "needs_practice"
      ? "border-l-red-400"
      : "border-l-amber-400";

  const zoneEmoji = point.mastery_zone === "needs_practice" ? "🔴" : "🟡";
  const zoneLabel = point.mastery_zone === "needs_practice" ? "需练习" : "学习中";

  const accPct = Math.round(point.accuracy * 100);
  const barColor =
    point.accuracy >= 0.6
      ? "bg-warm-400"
      : "bg-red-400";

  return (
    <div className={`rounded-lg border border-parchment-300 border-l-4 ${borderColor} bg-white p-3.5`}>
      <div className="flex items-center gap-2">
        <span className="text-xs">{zoneEmoji}</span>
        <Badge variant="outline" className="border-volcano-300 text-volcano-500 text-[10px] px-1.5">
          {point.error_code}
        </Badge>
        <span className="text-sm font-medium text-ink-500">
          {ERROR_LABELS[point.error_code as keyof typeof ERROR_LABELS] ?? point.error_code}
        </span>
      </div>

      <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <BookOpen className="h-3.5 w-3.5 shrink-0" />
        <span>{point.unit_title} · {point.knowledge_point}</span>
      </div>

      {point.typical_error && (
        <div className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
          <Lightbulb className="h-3.5 w-3.5 shrink-0 mt-0.5 text-warm-400" />
          <span>典型错误：{point.typical_error}</span>
        </div>
      )}

      <div className="mt-2.5 flex items-center gap-2.5">
        <span className="text-[11px] text-muted-foreground shrink-0">
          准确率
        </span>
        <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-parchment-200">
          <div
            className={`absolute left-0 top-0 h-full rounded-full ${barColor}`}
            style={{ width: `${accPct}%` }}
          />
        </div>
        <span className="text-xs font-medium text-ink-400 shrink-0 w-8 text-right">
          {accPct}%
        </span>
        <span className="text-[10px] text-muted-foreground shrink-0">
          ({point.total_attempts}次练习)
        </span>
      </div>
    </div>
  );
}

type DrawerTab = "overview" | "trajectory" | "profile";

interface StudentDetailDrawerProps {
  tree: StudentTree | null;
  onClose: () => void;
}

const TABS: { key: DrawerTab; label: string; icon: typeof BarChart3 }[] = [
  { key: "overview", label: "数据概览", icon: BarChart3 },
  { key: "trajectory", label: "错因轨迹", icon: Target },
  { key: "profile", label: "学习画像", icon: User },
];

const PERSONALITY_TAG_OPTIONS = [
  "细心", "粗心", "认真", "马虎", "善于思考",
  "勇于尝试", "需要鼓励", "容易放弃", "逻辑清晰", "需要引导",
] as const;

const LEARNING_STYLE_OPTIONS = [
  { value: "视觉型", label: "视觉型" },
  { value: "听觉型", label: "听觉型" },
  { value: "动手型", label: "动手型" },
  { value: "混合型", label: "混合型" },
] as const;

const GUIDANCE_MODE_OPTIONS = [
  { value: "standard", label: "标准模式" },
  { value: "exploration", label: "探索模式" },
  { value: "challenge", label: "挑战模式" },
] as const;

const TAG_COLORS: Record<string, string> = {
  "细心": "bg-forest-100 text-forest-700 border-forest-200",
  "粗心": "bg-volcano-100 text-volcano-500 border-volcano-200",
  "认真": "bg-forest-100 text-forest-700 border-forest-200",
  "马虎": "bg-volcano-100 text-volcano-500 border-volcano-200",
  "善于思考": "bg-sage-100 text-sage-700 border-sage-200",
  "勇于尝试": "bg-warm-100 text-warm-700 border-warm-200",
  "需要鼓励": "bg-volcano-50 text-volcano-400 border-volcano-200",
  "容易放弃": "bg-volcano-50 text-volcano-400 border-volcano-200",
  "逻辑清晰": "bg-sage-100 text-sage-700 border-sage-200",
  "需要引导": "bg-warm-50 text-warm-500 border-warm-200",
};

interface ProfileTabProps {
  tree: StudentTree;
  colors: ReturnType<typeof getTreeColors>;
  overallTrend: number;
}

function ProfileTab({ tree, colors, overallTrend }: ProfileTabProps) {
  const mutation = useUpdateStudentProfile();

  const [personalityTags, setPersonalityTags] = useState<string[]>([]);
  const [tagPickerOpen, setTagPickerOpen] = useState(false);
  const [learningStyle, setLearningStyle] = useState<string>("");
  const [guidanceMode, setGuidanceMode] = useState<string>("standard");
  const [notes, setNotes] = useState<string>("");
  const [notesDirty, setNotesDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const saveField = useCallback(
    (data: { personality_tags?: string[]; learning_style?: string; notes?: string }) => {
      setSaveStatus("saving");
      mutation.mutate(
        { studentId: tree.student_id, data },
        {
          onSuccess: () => {
            setSaveStatus("saved");
            setTimeout(() => setSaveStatus("idle"), 1500);
          },
          onError: () => {
            setSaveStatus("error");
            setTimeout(() => setSaveStatus("idle"), 2500);
          },
        },
      );
    },
    [mutation, tree.student_id],
  );

  const toggleTag = (tag: string) => {
    setPersonalityTags((prev) => {
      const next = prev.includes(tag)
        ? prev.filter((t) => t !== tag)
        : prev.length < 3
          ? [...prev, tag]
          : prev;
      if (next !== prev) saveField({ personality_tags: next });
      return next;
    });
  };

  const handleGuidanceModeChange = (value: string | null) => {
    if (!value) return;
    setGuidanceMode(value);
    saveField({ learning_style: learningStyle || undefined, notes: notes || undefined });
  };

  const handleLearningStyleChange = (value: string | null) => {
    if (!value) return;
    setLearningStyle(value);
    saveField({ learning_style: value });
  };

  const handleNotesBlur = () => {
    if (notesDirty) {
      setNotesDirty(false);
      saveField({ notes });
    }
  };

  return (
    <motion.div
      key="profile"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      className="space-y-6"
    >
      <div className="rounded-lg border border-parchment-300 bg-white p-4">
        <div className="flex items-center gap-3">
          <SvgTree
            stage={tree.current_stage}
            emotion={tree.emotional_state}
            colors={colors}
            size={80}
            animate
          />
          <div className="flex-1">
            <p className="font-medium text-ink-500">{getEmotionLabel(tree.emotional_state)}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {tree.emotional_state === "thriving" && "蓬勃发展！这棵小树正在茁壮成长，枝繁叶茂。"}
              {tree.emotional_state === "happy" && "状态不错，稳步前进中。继续保持节奏就好。"}
              {tree.emotional_state === "stable" && "平稳成长，不急不躁。每一天的坚持都在积累。"}
              {tree.emotional_state === "wilting" && "最近有点吃力，叶子开始发黄。多一些关注和陪伴。"}
              {tree.emotional_state === "struggling" && "遇到困难了，但没关系。放慢脚步，一步一步来。"}
            </p>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-medium text-ink-500">个性标签</h3>
          <span className="text-xs text-muted-foreground">{personalityTags.length}/3</span>
        </div>
        <div className="rounded-lg border border-parchment-300 bg-white p-4">
          <div className="flex flex-wrap gap-2">
            {personalityTags.map((tag) => (
              <span
                key={tag}
                className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TAG_COLORS[tag] ?? "bg-parchment-100 text-ink-400 border-parchment-300"}`}
              >
                {tag}
                <button
                  onClick={() => toggleTag(tag)}
                  className="ml-0.5 rounded-full p-0.5 hover:bg-black/10"
                  aria-label={`移除 ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {personalityTags.length < 3 && (
              <button
                onClick={() => setTagPickerOpen((o) => !o)}
                className="inline-flex items-center gap-1 rounded-full border border-dashed border-parchment-400 px-2.5 py-0.5 text-xs text-muted-foreground transition-colors hover:border-warm-400 hover:text-warm-500"
              >
                <Pencil className="h-3 w-3" />
                选择标签
              </button>
            )}
          </div>

          <AnimatePresence>
            {tagPickerOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-3 flex flex-wrap gap-1.5 border-t border-parchment-200 pt-3">
                  {PERSONALITY_TAG_OPTIONS.map((tag) => {
                    const selected = personalityTags.includes(tag);
                    const disabled = !selected && personalityTags.length >= 3;
                    return (
                      <button
                        key={tag}
                        onClick={() => !disabled && toggleTag(tag)}
                        disabled={disabled}
                        className={`rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                          selected
                            ? `${TAG_COLORS[tag] ?? "bg-forest-100 text-forest-700 border-forest-200"} ring-1 ring-warm-300`
                            : disabled
                              ? "border-parchment-200 bg-parchment-100 text-parchment-300 cursor-not-allowed"
                              : "border-parchment-300 bg-white text-ink-400 hover:border-warm-300 hover:text-warm-500"
                        }`}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <h3 className="mb-2 text-sm font-medium text-ink-500">学习风格</h3>
          <Select value={learningStyle || undefined} onValueChange={handleLearningStyleChange}>
            <SelectTrigger className="w-full border-parchment-300 bg-white text-sm">
              <SelectValue placeholder="选择风格" />
            </SelectTrigger>
            <SelectContent>
              {LEARNING_STYLE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <h3 className="mb-2 text-sm font-medium text-ink-500">引导模式</h3>
          <Select value={guidanceMode} onValueChange={handleGuidanceModeChange}>
            <SelectTrigger className="w-full border-parchment-300 bg-white text-sm">
              <SelectValue placeholder="选择模式" />
            </SelectTrigger>
            <SelectContent>
              {GUIDANCE_MODE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium text-ink-500">学习概况</h3>
        <div className="rounded-lg border border-parchment-300 bg-white p-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md bg-sage-50 p-2.5 text-center">
              <p className="text-xs text-muted-foreground">准确率趋势</p>
              <p className="mt-1 text-sm font-medium text-sage-500">
                {overallTrend > 0.05 ? "稳步上升" : overallTrend < -0.05 ? "需要关注" : "保持稳定"}
              </p>
            </div>
            <div className="rounded-md bg-warm-50 p-2.5 text-center">
              <p className="text-xs text-muted-foreground">练习频率</p>
              <p className="mt-1 text-sm font-medium text-warm-500">
                {tree.days_completed >= 20 ? "非常积极" : tree.days_completed >= 10 ? "按计划进行" : "需鼓励"}
              </p>
            </div>
            <div className="rounded-md bg-forest-50 p-2.5 text-center">
              <p className="text-xs text-muted-foreground">薄弱环节</p>
              <p className="mt-1 text-sm font-medium text-forest-700">
                {tree.dominant_errors.length > 0 ? tree.dominant_errors.slice(0, 2).join(", ") : "无"}
              </p>
            </div>
            <div className="rounded-md bg-volcano-50 p-2.5 text-center">
              <p className="text-xs text-muted-foreground">鼓励需求</p>
              <p className="mt-1 text-sm font-medium text-volcano-500">
                {tree.encouragement_needed ? "需要关怀" : "状态良好"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {tree.dominant_errors.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-ink-500">错因画像</h3>
          <div className="space-y-2">
            {tree.dominant_errors.map((code) => (
              <div key={code} className="flex items-center gap-2 rounded-lg border border-parchment-300 bg-white p-3">
                <Badge variant="outline" className="border-volcano-300 text-volcano-500">
                  {code}
                </Badge>
                <span className="text-sm text-ink-400">
                  {ERROR_LABELS[code as keyof typeof ERROR_LABELS] ?? ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="mb-2 text-sm font-medium text-ink-500">教师备注</h3>
        <Textarea
          value={notes}
          onChange={(e) => {
            setNotes(e.target.value);
            setNotesDirty(true);
          }}
          onBlur={handleNotesBlur}
          placeholder="记录关于这个孩子的观察和想法..."
          className="min-h-20 border-parchment-300 bg-white text-sm placeholder:text-parchment-400"
        />
      </div>

      <AnimatePresence>
        {saveStatus !== "idle" && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${
              saveStatus === "saving"
                ? "bg-warm-50 text-warm-500"
                : saveStatus === "saved"
                  ? "bg-forest-50 text-forest-600"
                  : "bg-volcano-50 text-volcano-500"
            }`}
          >
            {saveStatus === "saving" && <Loader2 className="h-3 w-3 animate-spin" />}
            {saveStatus === "saved" && <Check className="h-3 w-3" />}
            {saveStatus === "saving" && "保存中..."}
            {saveStatus === "saved" && "已保存"}
            {saveStatus === "error" && "保存失败，请重试"}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function StudentDetailDrawer({ tree, onClose }: StudentDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<DrawerTab>("overview");
  const colors = useMemo(
    () => tree ? getTreeColors(tree.tree_species_id || "cherry", tree.emotional_state, tree.emotional_intensity) : null,
    [tree],
  );
  const lastWeek = tree?.weekly_accuracy[tree.weekly_accuracy.length - 1];
  const firstWeek = tree?.weekly_accuracy[0];
  const overallTrend = lastWeek && firstWeek ? lastWeek.accuracy - firstWeek.accuracy : 0;

  const profileQuery = useQuery({
    queryKey: ["studentProfile", tree?.student_id],
    queryFn: () => getStudentProfile(tree!.student_id),
    enabled: !!tree?.student_id,
  });
  const errorAccuracyMap = profileQuery.data?.accuracy_by_error_code ?? {};
  const totalDiagnoses = profileQuery.data?.total_attempts ?? 0;
  const weakPoints = profileQuery.data?.weak_knowledge_points ?? [];
  const studentInfo = profileQuery.data?.student ?? null;
  const sortedWeakPoints = useMemo(
    () =>
      weakPoints
        .filter((p) => p.mastery_zone !== "mastered")
        .sort((a, b) => a.accuracy - b.accuracy)
        .slice(0, 5),
    [weakPoints],
  );

  const masteryQuery = useQuery({
    queryKey: ["studentMastery", tree?.student_id],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/students/${tree!.student_id}/mastery`);
      if (!res.ok) throw new Error("Failed to fetch mastery");
      return res.json() as Promise<{
        student_id: string;
        error_codes: Record<string, {
          mastery_probability: number;
          zone: string;
          total_attempts: number;
          correct_count: number;
        }>;
        overall_mastery: number;
        mastered_count: number;
        total_error_codes: number;
        review_status: string;
      }>;
    },
    enabled: !!tree?.student_id,
  });
  const masteryData = masteryQuery.data;

  const errorDistribution = useMemo(() => {
    if (!tree) return [];
    return tree.dominant_errors.map((code) => ({
      code,
      label: ERROR_LABELS[code as keyof typeof ERROR_LABELS] ?? code,
      severity: code === "E99" ? "low" : "medium" as const,
    }));
  }, [tree]);

  return (
    <AnimatePresence>
      {tree && colors && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col overflow-hidden bg-parchment-50 shadow-2xl"
          >
            <div className="flex shrink-0 items-center justify-between border-b border-parchment-300 bg-parchment-100/95 px-6 py-4 backdrop-blur">
              <div className="flex items-center gap-4">
                <SvgTree
                  stage={tree.current_stage}
                  emotion={tree.emotional_state}
                  colors={colors}
                  size={50}
                  animate
                />
                <div>
                  <h2 className="text-lg font-bold text-ink-500">{tree.student_name}</h2>
                  <p className="text-sm text-ink-300">
                    {tree.tree_species_name} · {getStageLabel(tree.current_stage)} · {getEmotionEmoji(tree.emotional_state)} {getEmotionLabel(tree.emotional_state)}
                  </p>
                </div>
              </div>
              <button onClick={onClose} className="rounded-full p-2 hover:bg-parchment-200" aria-label="关闭详情">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex shrink-0 border-b border-parchment-300 bg-parchment-100/80">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button aria-label={tab.label}
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex flex-1 items-center justify-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-colors ${
                      activeTab === tab.key
                        ? "border-b-2 border-warm-400 text-warm-500"
                        : "text-ink-300 hover:text-ink-500"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              <AnimatePresence mode="wait">
                {activeTab === "overview" && (
                  <motion.div
                    key="overview"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="space-y-6"
                  >
                    {studentInfo && (
                      <div className="flex items-center justify-between rounded-lg border border-parchment-300 bg-white px-4 py-3">
                        <div>
                          <h3 className="text-base font-bold text-ink-500">{studentInfo.name}</h3>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {getGradeLabel(studentInfo.grade)} · {studentInfo.class_id}班{studentInfo.student_number ? ` · 学号${studentInfo.student_number}` : ""}
                          </p>
                        </div>
                        <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${accuracyBadgeColor(tree.overall_accuracy)}`}>
                          {Math.round(tree.overall_accuracy * 100)}%
                        </span>
                      </div>
                    )}

                    <div className="grid grid-cols-3 gap-3">
                      <Card size="sm">
                        <CardContent className="pt-3 text-center">
                          <p className={`text-2xl font-bold ${tree.overall_accuracy >= 0.8 ? "text-forest-600" : tree.overall_accuracy >= 0.6 ? "text-warm-500" : "text-volcano-400"}`}>
                            {Math.round(tree.overall_accuracy * 100)}%
                          </p>
                          <p className="text-xs text-muted-foreground">总准确率</p>
                        </CardContent>
                      </Card>
                      <Card size="sm">
                        <CardContent className="pt-3 text-center">
                          <p className="text-2xl font-bold text-ink-500">{tree.correct_count}/{tree.total_attempts}</p>
                          <p className="text-xs text-muted-foreground">正确/总题</p>
                        </CardContent>
                      </Card>
                      <Card size="sm">
                        <CardContent className="pt-3 text-center">
                          <p className="text-2xl font-bold text-ink-500">{tree.days_completed}</p>
                          <p className="text-xs text-muted-foreground">练习天数</p>
                        </CardContent>
                      </Card>
                    </div>

                    {tree.encouragement_needed && (
                      <div className="rounded-lg border border-volcano-200 bg-volcano-50 p-3">
                        <p className="text-sm font-medium text-volcano-500">
                          这个小朋友最近遇到了困难，准确率在下降。多一些耐心和鼓励，帮他重新找回节奏。
                        </p>
                      </div>
                    )}

                    <div>
                      <h3 className="mb-2 text-sm font-medium text-ink-500">趋势</h3>
                      <div className="flex items-center gap-2">
                        <TrendIcon current={lastWeek?.accuracy ?? 0} previous={firstWeek?.accuracy ?? 0} />
                        <span className="text-sm">
                          {overallTrend > 0.05 ? "持续进步中" : overallTrend < -0.05 ? "需要关注" : "保持稳定"}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h3 className="mb-3 text-sm font-medium text-ink-500">错因能力图谱</h3>
                      <p className="mb-2 text-xs text-muted-foreground">
                        基于 {totalDiagnoses} 次诊断记录 · 虚线为60%危险线
                      </p>
                      <ErrorRadarChart accuracyByErrorCode={errorAccuracyMap} />
                    </div>

                    {masteryData && (
                      <div>
                        <h3 className="mb-3 text-sm font-medium text-ink-500">掌握度总览</h3>
                        <div className="space-y-3">
                          <div>
                            <div className="mb-1 flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">总体掌握度</span>
                              <span className="font-medium text-ink-500">
                                {Math.round(masteryData.overall_mastery * 100)}%
                              </span>
                            </div>
                            <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-parchment-300">
                              <motion.div
                                className="absolute left-0 top-0 h-full rounded-full bg-forest-500"
                                initial={{ width: 0 }}
                                animate={{ width: `${masteryData.overall_mastery * 100}%` }}
                                transition={{ delay: 0.2, duration: 0.7 }}
                              />
                            </div>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              已掌握 {masteryData.mastered_count} / {masteryData.total_error_codes} 个错因类型
                            </p>
                          </div>

                          <div className="grid grid-cols-3 gap-2">
                            {([
                              {
                                zone: "mastered" as const,
                                label: "已掌握",
                                emoji: "🟢",
                                bgClass: "bg-forest-50 border-forest-200",
                                textClass: "text-forest-700",
                              },
                              {
                                zone: "learning" as const,
                                label: "学习中",
                                emoji: "🟡",
                                bgClass: "bg-warm-50 border-warm-200",
                                textClass: "text-warm-700",
                              },
                              {
                                zone: "needs_practice" as const,
                                label: "需练习",
                                emoji: "🔴",
                                bgClass: "bg-volcano-50 border-volcano-200",
                                textClass: "text-volcano-500",
                              },
                            ] as const).map(({ zone, label, emoji, bgClass, textClass }) => {
                              const codes = Object.entries(masteryData.error_codes)
                                .filter(([, v]) => v.zone === zone)
                                .map(([code]) => code);
                              if (codes.length === 0) return null;
                              return (
                                <div
                                  key={zone}
                                  className={`rounded-lg border p-2.5 ${bgClass}`}
                                >
                                  <div className="flex items-center gap-1">
                                    <span className="text-xs">{emoji}</span>
                                    <span className={`text-xs font-medium ${textClass}`}>
                                      {label}
                                    </span>
                                    <span className={`ml-auto text-xs font-bold ${textClass}`}>
                                      {codes.length}
                                    </span>
                                  </div>
                                  <div className="mt-1.5 flex flex-wrap gap-1">
                                    {codes.map((code) => (
                                      <span
                                        key={code}
                                        className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-medium ${textClass} bg-white/60`}
                                      >
                                        {code}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {sortedWeakPoints.length > 0 && (
                      <div>
                        <div className="mb-3 flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-volcano-400" />
                          <h3 className="text-sm font-medium text-ink-500">薄弱知识点</h3>
                          <span className="text-[11px] text-muted-foreground">按准确率升序</span>
                        </div>
                        <div className="space-y-2.5">
                          {sortedWeakPoints.map((point) => (
                            <WeakKnowledgeCard key={`${point.error_code}-${point.unit_id}`} point={point} />
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h3 className="mb-3 text-sm font-medium text-ink-500">周准确率变化</h3>
                      <AccuracyTrendChart data={tree.weekly_accuracy} />
                    </div>

                    <div>
                      <h3 className="mb-3 text-sm font-medium text-ink-500">作业周历</h3>
                      <div className="grid grid-cols-8 gap-1.5">
                        {tree.weekly_accuracy.map((w) => {
                          const acc = w.accuracy;
                          let bg = "bg-volcano-100 text-volcano-500";
                          if (acc >= 0.8) bg = "bg-forest-100 text-forest-700";
                          else if (acc >= 0.6) bg = "bg-warm-100 text-warm-500";
                          return (
                            <div key={w.week_number} className={`flex flex-col items-center rounded-md p-1.5 text-xs ${bg}`}>
                              <span className="font-medium">W{w.week_number}</span>
                              <span>{Math.round(acc * 100)}%</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div>
                      <h3 className="mb-3 text-sm font-medium text-ink-500">成长进度</h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{tree.days_completed} / {tree.total_days} 天</span>
                          <span className="font-medium">{getStageLabel(tree.current_stage)}</span>
                        </div>
                        <div className="relative h-2 w-full overflow-hidden rounded-full bg-parchment-300">
                          <motion.div
                            className="absolute left-0 top-0 h-full rounded-full bg-forest-500"
                            initial={{ width: 0 }}
                            animate={{ width: `${(tree.days_completed / tree.total_days) * 100}%` }}
                            transition={{ delay: 0.3, duration: 0.8 }}
                          />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === "trajectory" && (
                  <motion.div
                    key="trajectory"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="space-y-4"
                  >
                    <h3 className="text-sm font-medium text-ink-500">错因时间线</h3>
                    {errorDistribution.length > 0 ? (
                      <div className="space-y-3">
                        {errorDistribution.map((err, i) => (
                          <div key={err.code} className="flex items-start gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warm-100 text-xs font-bold text-warm-500">
                              {i + 1}
                            </div>
                            <div className="flex-1 rounded-lg border border-parchment-300 bg-white p-3">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="border-volcano-300 text-volcano-500 text-xs">
                                  {err.code}
                                </Badge>
                                <span className="text-sm font-medium text-ink-500">{err.label}</span>
                              </div>
                              <p className="mt-1 text-xs text-muted-foreground">
                                需要通过针对性练习巩固此知识点
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-lg border border-parchment-300 bg-white p-6 text-center">
                        <p className="text-sm text-muted-foreground">暂无错因记录</p>
                      </div>
                    )}

                    <h3 className="pt-2 text-sm font-medium text-ink-500">周度准确率走势</h3>
                    <div className="space-y-2">
                      {tree.weekly_accuracy.map((w) => (
                        <div key={w.week_number} className="flex items-center gap-3">
                          <span className="w-8 text-xs text-muted-foreground">W{w.week_number}</span>
                          <div className="relative h-4 flex-1 overflow-hidden rounded-full bg-parchment-200">
                            <motion.div
                              className="absolute left-0 top-0 h-full rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${w.accuracy * 100}%` }}
                              transition={{ delay: 0.1, duration: 0.6 }}
                              style={{
                                backgroundColor: w.accuracy >= 0.8 ? "#46803c" : w.accuracy >= 0.6 ? "#d4a843" : "#e8945a",
                              }}
                            />
                          </div>
                          <span className="w-10 text-right text-xs font-medium text-ink-400">
                            {Math.round(w.accuracy * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {activeTab === "profile" && (
                  <ProfileTab tree={tree} colors={colors} overallTrend={overallTrend} />
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
