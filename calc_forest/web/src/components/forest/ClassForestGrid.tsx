"use client";

import { useState, useMemo, useCallback } from "react";
import { Trees, Maximize2, Grid3X3 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { StudentTreeCard } from "./StudentTreeCard";
import dynamic from "next/dynamic";
import { ForestBackground } from "./ForestBackground";
import type { ClassForestResponse, StudentTree } from "@/lib/types";
import { getEmotionLabel, getEmotionEmoji } from "./trees/useEmotionState";

const StudentDetailDrawer = dynamic(
  () => import("./StudentDetailDrawer").then((m) => ({ default: m.StudentDetailDrawer })),
  { ssr: false },
);

type ZoomMode = "thumbnail" | "expanded";

interface ClassForestGridProps {
  forest: ClassForestResponse;
}

export function ClassForestGrid({ forest }: ClassForestGridProps) {
  const [selectedTree, setSelectedTree] = useState<StudentTree | null>(null);
  const [zoomMode, setZoomMode] = useState<ZoomMode>("expanded");

  const thumbnailSubset = useMemo(() => {
    const shuffled = [...forest.trees].sort(() => {
      return (Math.sin(forest.trees.length) * 10000) % 1 - 0.5;
    });
    return shuffled.slice(0, Math.min(6, forest.trees.length));
  }, [forest.trees]);

  const displayTrees = zoomMode === "thumbnail" ? thumbnailSubset : forest.trees;

  const handleTreeClick = useCallback((tree: StudentTree) => {
    setSelectedTree(tree);
  }, []);

  const handleClose = useCallback(() => {
    setSelectedTree(null);
  }, []);

  const classAccColor =
    forest.class_accuracy >= 0.8
      ? "text-forest-600"
      : forest.class_accuracy >= 0.6
        ? "text-amber-600"
        : "text-fruit-600";

  return (
    <ForestBackground emotion={forest.class_emotional_state}>
      <div className="space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2 text-xl font-bold">
              <Trees className="h-5 w-5 text-forest-600" />
              {forest.class_name}
            </h2>
            <p className="text-sm text-muted-foreground">
              {forest.academic_year} {forest.semester} · {forest.week_number != null ? `第 ${forest.week_number} 周` : "未开课"}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className={`text-2xl font-bold ${classAccColor}`}>
                {Math.round(forest.class_accuracy * 100)}%
              </p>
              <p className="text-xs text-muted-foreground">班级平均</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-2xl font-bold">{forest.trees.length}</p>
              <p className="text-xs text-muted-foreground">棵小树</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="flex flex-col gap-1">
              <p className="text-xs text-muted-foreground">班级氛围</p>
              <Badge
                variant="outline"
                className={`text-xs ${
                  forest.class_emotional_state === "thriving" ? "border-amber-300 text-amber-700" :
                  forest.class_emotional_state === "struggling" ? "border-slate-300 text-slate-500" :
                  "border-forest-300 text-forest-700"
                }`}
              >
                {getEmotionEmoji(forest.class_emotional_state)} {getEmotionLabel(forest.class_emotional_state)}
              </Badge>
            </div>
            {forest.class_top_errors.length > 0 && (
              <>
                <div className="h-8 w-px bg-border" />
                <div className="flex flex-col gap-1">
                  <p className="text-xs text-muted-foreground">常见错因</p>
                  <div className="flex gap-1">
                    {forest.class_top_errors.map((code) => (
                      <Badge key={code} variant="outline" className="border-amber-300 text-xs text-amber-700">
                        {code}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
            <div className="h-8 w-px bg-border" />
            <div className="flex items-center gap-1 rounded-lg border bg-parchment-50 p-1">
              <button
                onClick={() => setZoomMode("expanded")}
                className={`rounded-md p-1.5 transition-colors ${zoomMode === "expanded" ? "bg-warm-400 text-white" : "text-muted-foreground hover:text-foreground"}`}
                title="展开视图"
                aria-label="展开视图"
                aria-pressed={zoomMode === "expanded"}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setZoomMode("thumbnail")}
                className={`rounded-md p-1.5 transition-colors ${zoomMode === "thumbnail" ? "bg-warm-400 text-white" : "text-muted-foreground hover:text-foreground"}`}
                title="缩略视图"
                aria-label="缩略视图"
                aria-pressed={zoomMode === "thumbnail"}
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <motion.div
          className={`grid gap-5 ${
            zoomMode === "thumbnail"
              ? "grid-cols-3 sm:grid-cols-4 md:grid-cols-6"
              : "grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
          }`}
        >
          <AnimatePresence mode="popLayout">
            {displayTrees.map((tree, i) => (
              <StudentTreeCard
                key={tree.student_id}
                tree={tree}
                index={i}
                onClick={() => handleTreeClick(tree)}
                compact={zoomMode === "thumbnail"}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      </div>

      <StudentDetailDrawer
        tree={selectedTree}
        onClose={handleClose}
      />
    </ForestBackground>
  );
}
