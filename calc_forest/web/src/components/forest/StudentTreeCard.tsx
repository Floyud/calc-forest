"use client";

import { useMemo, memo, useState } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { SvgTree } from "./trees/SvgTree";
import { CanvasTree } from "./canvas/CanvasTreeCard";
import { getTreeColors } from "./trees/treeColors";
import { getEmotionLabel, getEmotionEmoji } from "./trees/useEmotionState";
import type { StudentTree, EmotionState } from "@/lib/types";

const USE_CANVAS = process.env.NEXT_PUBLIC_USE_CANVAS !== "false";

function accuracyColor(acc: number): string {
  if (acc >= 0.8) return "text-forest-600";
  if (acc >= 0.6) return "text-amber-600";
  return "text-fruit-600";
}

function emotionBorderClass(emotion: EmotionState): string {
  switch (emotion) {
    case "thriving": return "border-amber-300/80 ring-1 ring-amber-200/50";
    case "happy": return "border-forest-300/80 ring-1 ring-forest-200/30";
    case "stable": return "border-forest-200/60";
    case "wilting": return "border-amber-200/60";
    case "struggling": return "border-slate-300/60 ring-1 ring-slate-200/40";
    default: return "border-forest-200/60";
  }
}

function emotionBgClass(emotion: EmotionState): string {
  switch (emotion) {
    case "thriving": return "bg-gradient-to-b from-amber-50/80 to-white";
    case "happy": return "bg-gradient-to-b from-forest-50/50 to-white";
    case "stable": return "bg-white";
    case "wilting": return "bg-gradient-to-b from-amber-50/30 to-white";
    case "struggling": return "bg-gradient-to-b from-slate-50/50 to-white";
    default: return "bg-white";
  }
}

interface StudentTreeCardProps {
  tree: StudentTree;
  onClick: () => void;
  index: number;
  compact?: boolean;
  useCanvas?: boolean;
}

export const StudentTreeCard = memo(function StudentTreeCard({ tree, onClick, index, compact = false, useCanvas }: StudentTreeCardProps) {
  const [canvasFailed, setCanvasFailed] = useState(false);
  const effectiveStage = tree.current_stage;
  const effectiveSpecies = tree.tree_species_id ?? "cherry";
  const effectiveEmotion: EmotionState = tree.emotional_state;

  const accColor = accuracyColor(tree.overall_accuracy);
  const colors = useMemo(
    () => getTreeColors(effectiveSpecies, effectiveEmotion, tree.emotional_intensity),
    [effectiveSpecies, effectiveEmotion, tree.emotional_intensity],
  );

  const trend = useMemo(() => {
    const lastWeek = tree.weekly_accuracy[tree.weekly_accuracy.length - 1];
    const prevWeek = tree.weekly_accuracy.length >= 2 ? tree.weekly_accuracy[tree.weekly_accuracy.length - 2] : null;
    if (!lastWeek || !prevWeek) return { icon: "\u2194", color: "text-muted-foreground" };
    const diff = lastWeek.accuracy - prevWeek.accuracy;
    if (diff > 0.05) return { icon: "\u2191", color: "text-forest-600" };
    if (diff < -0.05) return { icon: "\u2193", color: "text-fruit-600" };
    return { icon: "\u2194", color: "text-muted-foreground" };
  }, [tree.weekly_accuracy]);

  const progressColor = tree.overall_accuracy >= 0.8 ? "#46803c" : tree.overall_accuracy >= 0.6 ? "#ca8a04" : "#ea580c";

  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ delay: index * 0.04, type: "spring", stiffness: 120, damping: 20 }}
      whileHover={{ scale: 1.04, y: -3 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      aria-label={`${tree.student_name} ${getEmotionLabel(effectiveEmotion)}`}
      className={`group relative flex flex-col items-center gap-2 rounded-2xl border p-4 text-center shadow-sm transition-shadow duration-300 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${compact ? "p-2.5" : "p-4"} ${emotionBorderClass(effectiveEmotion)} ${emotionBgClass(effectiveEmotion)}`}
      style={{ contain: "layout style paint" }}
    >
      {!compact && (
        <div className="absolute right-2 top-2 flex flex-col items-end gap-1">
          <span className={`text-xs font-bold ${trend.color}`}>{trend.icon}</span>
          {tree.encouragement_needed && (
            <span className="text-[10px] text-fruit-500 font-medium">需要关怀</span>
          )}
        </div>
      )}

      <div className={`transition-transform duration-300 group-hover:scale-105 ${compact ? "scale-75" : ""}`}>
        {(useCanvas ?? USE_CANVAS) && !canvasFailed ? (
          <CanvasTree
            stage={effectiveStage}
            emotion={effectiveEmotion}
            colors={colors}
            size={compact ? 60 : 100}
            animate
            index={index}
            onError={() => setCanvasFailed(true)}
          />
        ) : (
          <SvgTree
            stage={effectiveStage}
            emotion={effectiveEmotion}
            colors={colors}
            size={compact ? 60 : 100}
            animate
          />
        )}
      </div>

      <span className={`font-medium ${compact ? "text-xs" : "text-sm"}`}>{tree.student_name}</span>

      {!compact && (
        <div className="flex items-center gap-1">
          <Badge
            variant="outline"
            className={`text-[10px] ${
              effectiveEmotion === "thriving" ? "border-amber-300 text-amber-700 bg-amber-50" :
              effectiveEmotion === "happy" ? "border-forest-300 text-forest-700 bg-forest-50" :
              effectiveEmotion === "wilting" ? "border-amber-200 text-amber-600 bg-amber-50/50" :
              effectiveEmotion === "struggling" ? "border-slate-300 text-slate-500 bg-slate-50" :
              "border-forest-200 text-forest-600"
            }`}
          >
            {getEmotionEmoji(effectiveEmotion)} {getEmotionLabel(effectiveEmotion)}
          </Badge>
        </div>
      )}

      <div className="w-full">
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {tree.correct_count}/{tree.total_attempts} 题
          </span>
          <span className={`font-bold ${accColor}`}>
            {Math.round(tree.overall_accuracy * 100)}%
          </span>
        </div>
        <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="absolute left-0 top-0 h-full rounded-full"
            style={{
              backgroundColor: progressColor,
              width: `${tree.overall_accuracy * 100}%`,
              animation: "grow-x 0.8s ease-out both",
              animationDelay: `${0.5 + index * 0.03}s`,
              willChange: "transform",
            }}
          />
        </div>
      </div>

      {!compact && tree.dominant_errors.length > 0 && (
        <div className="mt-1 flex flex-wrap justify-center gap-1">
          {tree.dominant_errors.slice(0, 2).map((code) => (
            <span
              key={code}
              className="rounded bg-warm-100 px-1.5 py-0.5 text-[10px] text-warm-500"
            >
              {code}
            </span>
          ))}
        </div>
      )}
    </motion.button>
  );
});
