"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, Loader2, Check, Pencil, BookOpen, Lightbulb,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateStudentProfile } from "@/lib/api/hooks";
import { SvgTree } from "../trees/SvgTree";
import { getTreeColors } from "../trees/treeColors";
import { getEmotionLabel } from "../trees/useEmotionState";
import type { StudentTree } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";

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

export interface ProfileTabProps {
  tree: StudentTree;
  colors: ReturnType<typeof getTreeColors>;
  overallTrend: number;
  initialPersonalityTags: string[];
  initialLearningStyle: string;
  initialNotes: string;
  initialGuidanceMode: string;
}

export function ProfileTab({ tree, colors, overallTrend, initialPersonalityTags, initialLearningStyle, initialNotes, initialGuidanceMode }: ProfileTabProps) {
  const mutation = useUpdateStudentProfile();

  const [personalityTags, setPersonalityTags] = useState<string[]>(initialPersonalityTags);
  const [tagPickerOpen, setTagPickerOpen] = useState(false);
  const [learningStyle, setLearningStyle] = useState<string>(initialLearningStyle);
  const [guidanceMode, setGuidanceMode] = useState<string>(initialGuidanceMode);
  const [notes, setNotes] = useState<string>(initialNotes);
  const [notesDirty, setNotesDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  useEffect(() => {
    setPersonalityTags(initialPersonalityTags);
    setLearningStyle(initialLearningStyle);
    setNotes(initialNotes);
    setGuidanceMode(initialGuidanceMode);
  }, [initialPersonalityTags, initialLearningStyle, initialNotes, initialGuidanceMode]);

  const saveField = useCallback(
    (data: { personality_tags?: string[]; learning_style?: string; notes?: string; guidance_mode?: string }) => {
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
    saveField({ guidance_mode: value });
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
