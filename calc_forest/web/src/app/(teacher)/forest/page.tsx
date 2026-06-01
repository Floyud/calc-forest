"use client";

import React, { useMemo, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import dynamic from "next/dynamic";
import { Trees, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ClassForestGrid } from "@/components/forest/ClassForestGrid";
import { ForestBackground } from "@/components/forest/ForestBackground";
import { SvgTree } from "@/components/forest/trees/SvgTree";
import { getTreeColors } from "@/components/forest/trees/treeColors";
import { getEmotionLabel, getEmotionEmoji } from "@/components/forest/trees/useEmotionState";
import { useClassForest } from "@/lib/api/hooks";
import { DEFAULT_CLASS_ID } from "@/lib/config";
import type { StudentTree } from "@/lib/types";

const StudentDetailDrawer = dynamic(
  () => import("@/components/forest/StudentDetailDrawer").then((m) => ({ default: m.StudentDetailDrawer })),
  { ssr: false },
);

/* ─── Hero Landscape Tree ─── */
function LandscapeTree({
  tree,
  x,
  y,
  size,
  delay,
  onClick,
}: {
  tree: StudentTree;
  x: string;
  y: string;
  size: number;
  delay: number;
  onClick: () => void;
}) {
  const colors = useMemo(
    () => getTreeColors(tree.tree_species_id || "cherry", tree.emotional_state, tree.emotional_intensity),
    [tree.tree_species_id, tree.emotional_state, tree.emotional_intensity],
  );

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.3, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay, duration: 0.7, type: "spring", stiffness: 100, damping: 12 }}
      onClick={onClick}
      className="group absolute cursor-pointer"
      style={{ left: x, bottom: y, transform: "translateX(-50%)" }}
      title={`${tree.student_name} — ${Math.round(tree.overall_accuracy * 100)}%`}
    >
      <div className="relative transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-2">
        <div className="drop-shadow-md">
          <SvgTree
            stage={tree.current_stage}
            emotion={tree.emotional_state}
            colors={colors}
            size={size}
            animate
          />
        </div>

        <div className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-xl bg-white/90 px-3 py-1 text-xs font-medium text-ink-400 opacity-0 shadow-sm backdrop-blur-sm transition-opacity duration-200 group-hover:opacity-100">
          {tree.student_name}
          <span className="ml-1.5 font-bold" style={{ color: tree.overall_accuracy >= 0.8 ? "#46803c" : tree.overall_accuracy >= 0.6 ? "#ca8a04" : "#ea580c" }}>
            {Math.round(tree.overall_accuracy * 100)}%
          </span>
        </div>
      </div>
    </motion.button>
  );
}

/* ─── Decorative Cloud ─── */
function FloatingCloud({ delay, duration, top, opacity }: { delay: number; duration: number; top: string; opacity: number }) {
  return (
    <div
      className="pointer-events-none absolute"
      style={{
        top,
        left: "-15%",
        opacity,
        animation: `cloud-drift ${duration}s ${delay}s infinite linear`,
      }}
    >
      <svg width="120" height="40" viewBox="0 0 120 40" fill="none">
        <ellipse cx="60" cy="28" rx="50" ry="12" fill="white" />
        <ellipse cx="40" cy="22" rx="30" ry="14" fill="white" />
        <ellipse cx="80" cy="24" rx="28" ry="11" fill="white" />
      </svg>
    </div>
  );
}

/* ─── Stat Pill ─── */
function StatPill({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="flex flex-col items-center gap-0.5 rounded-2xl bg-white/70 px-5 py-2.5 backdrop-blur-sm">
      <span className={`text-xl font-bold ${accent ?? "text-foreground"}`}>{value}</span>
      <span className="text-[11px] tracking-wide text-muted-foreground">{label}</span>
    </div>
  );
}

/* ─── Main Page ─── */
export default function ForestPage() {
  const { data: forest, isLoading, isError } = useClassForest(DEFAULT_CLASS_ID);
  const [selectedTree, setSelectedTree] = useState<StudentTree | null>(null);

  const handleHeroTreeClick = useCallback((tree: StudentTree) => {
    setSelectedTree(tree);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedTree(null);
  }, []);

  const landscapeTrees = useMemo(() => {
    if (!forest) return [];
    const trees = forest.trees;
    const count = Math.min(10, trees.length);
    const sorted = [...trees].sort((a, b) => a.student_id.localeCompare(b.student_id));
    const picked = sorted.slice(0, count);
    return picked.map((tree, i) => {
      const col = i % 5;
      const row = Math.floor(i / 5);
      const seed = tree.student_id.charCodeAt(tree.student_id.length - 1);
      const scatterX = ((seed * 7) % 10) - 5;
      const scatterY = ((seed * 13) % 8) - 4;
      const xPercent = 10 + col * 18 + scatterX;
      const yPercent = 8 + row * 22 + scatterY;
      const size = tree.current_stage === "mature" || tree.current_stage === "flowering" ? 80
        : tree.current_stage === "seed" || tree.current_stage === "sprout" ? 50
        : 65;
      return { tree, x: `${xPercent}%`, y: `${yPercent}%`, size, delay: 0.1 + i * 0.08 };
    });
  }, [forest]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 md:py-8 space-y-8">
        <div className="space-y-4">
          <div className="h-10 w-64 animate-pulse rounded-lg bg-muted" />
          <div className="h-[340px] animate-pulse rounded-xl bg-forest-100 md:h-[420px]" />
        </div>
      </div>
    );
  }

  if (isError || !forest) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50/50 p-10 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-red-700">无法加载班级森林</h2>
          <p className="text-sm text-red-600">
            请确认后端服务正在运行并已播种班级数据（G6C1）
          </p>
        </div>
      </div>
    );
  }

  const classAccColor = forest.class_accuracy >= 0.8
    ? "text-forest-600"
    : forest.class_accuracy >= 0.6
      ? "text-amber-600"
      : "text-fruit-600";

  const thrivingCount = forest.trees.filter(t => t.emotional_state === "thriving" || t.emotional_state === "happy").length;
  const needCareCount = forest.trees.filter(t => t.emotional_state === "wilting" || t.emotional_state === "struggling").length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:py-8 space-y-8">
      {/* ── Hero: Forest Landscape ── */}
      <motion.section
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-forest-100">
            <Trees className="h-5 w-5 text-forest-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground md:text-3xl">
              班级林园
              <span className="ml-2 text-lg font-medium text-muted-foreground md:text-xl">— {forest.class_name}</span>
            </h1>
            <p className="text-sm text-muted-foreground">
              {forest.academic_year} {forest.semester} · {forest.week_number != null ? `第 ${forest.week_number} 周` : "未开课"}
            </p>
          </div>
        </div>

        <ForestBackground emotion={forest.class_emotional_state}>
          <div className="relative h-[340px] md:h-[420px]">
            <FloatingCloud delay={0} duration={45} top="6%" opacity={0.5} />
            <FloatingCloud delay={15} duration={55} top="14%" opacity={0.35} />
            <FloatingCloud delay={30} duration={40} top="3%" opacity={0.25} />

            {landscapeTrees.map(({ tree, x, y, size, delay }) => (
              <LandscapeTree
                key={tree.student_id}
                tree={tree}
                x={x}
                y={y}
                size={size}
                delay={delay}
                onClick={() => handleHeroTreeClick(tree)}
              />
            ))}

            {/* Ground grass layers */}
            <div className="pointer-events-none absolute bottom-0 left-0 right-0">
              <svg viewBox="0 0 1200 80" className="w-full" preserveAspectRatio="none">
                <path
                  d="M0,30 Q50,15 100,28 Q150,40 200,25 Q250,12 300,30 Q350,45 400,28 Q450,15 500,32 Q550,45 600,26 Q650,12 700,30 Q750,42 800,25 Q850,14 900,32 Q950,44 1000,28 Q1050,15 1100,30 Q1150,42 1200,30 L1200,80 L0,80 Z"
                  fill="#86efac"
                  opacity="0.5"
                />
                <path
                  d="M0,40 Q100,28 200,38 Q300,50 400,35 Q500,22 600,40 Q700,52 800,36 Q900,25 1000,42 Q1100,52 1200,38 L1200,80 L0,80 Z"
                  fill="#4ade80"
                  opacity="0.35"
                />
                <path
                  d="M0,55 Q150,45 300,52 Q450,60 600,50 Q750,42 900,55 Q1050,60 1200,50 L1200,80 L0,80 Z"
                  fill="#22c55e"
                  opacity="0.2"
                />
              </svg>
            </div>
          </div>

          {/* Class stats bar at bottom of hero */}
          <div className="flex flex-wrap items-center justify-center gap-3 px-4 pb-5">
            <StatPill
              label="班级平均"
              value={`${Math.round(forest.class_accuracy * 100)}%`}
              accent={classAccColor}
            />
            <StatPill label="棵小树" value={`${forest.trees.length}`} />
            <StatPill
              label="蓬勃发展"
              value={`${thrivingCount}`}
              accent="text-forest-600"
            />
            {needCareCount > 0 && (
              <StatPill
                label="需要关怀"
                value={`${needCareCount}`}
                accent="text-amber-600"
              />
            )}
            <div className="flex flex-col items-center gap-0.5 rounded-2xl bg-white/70 px-5 py-2.5 backdrop-blur-sm">
              <Badge
                variant="outline"
                className={`text-xs ${
                  forest.class_emotional_state === "thriving" ? "border-amber-300 text-amber-700 bg-amber-50" :
                  forest.class_emotional_state === "happy" ? "border-forest-300 text-forest-700 bg-forest-50" :
                  forest.class_emotional_state === "wilting" ? "border-amber-200 text-amber-600 bg-amber-50/50" :
                  forest.class_emotional_state === "struggling" ? "border-slate-300 text-slate-500 bg-slate-50" :
                  "border-forest-200 text-forest-600 bg-forest-50/50"
                }`}
              >
                {getEmotionEmoji(forest.class_emotional_state)} {getEmotionLabel(forest.class_emotional_state)}
              </Badge>
              <span className="text-[11px] tracking-wide text-muted-foreground">班级氛围</span>
            </div>
            {forest.class_top_errors.length > 0 && (
              <div className="flex flex-col items-center gap-1 rounded-2xl bg-white/70 px-5 py-2.5 backdrop-blur-sm">
                <span className="text-[11px] tracking-wide text-muted-foreground">常见错因</span>
                <div className="flex gap-1">
                  {forest.class_top_errors.slice(0, 3).map((code) => (
                    <Badge key={code} variant="outline" className="border-amber-300 text-xs text-amber-700">
                      {code}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ForestBackground>
      </motion.section>

      {/* ── Expanded View: All Students Grid ── */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <div className="mb-4 flex items-center gap-2">
          <span className="text-xl">🌲</span>
          <h2 className="text-lg font-bold text-foreground">查看所有同学的小树</h2>
          <span className="text-sm text-muted-foreground">点击小树查看详细成长记录</span>
        </div>

        <ClassForestGrid forest={forest} />
      </motion.section>

      {/* ── Student Detail Drawer ── */}
      <AnimatePresence>
        {selectedTree && (
          <StudentDetailDrawer
            tree={selectedTree}
            onClose={handleCloseDrawer}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
