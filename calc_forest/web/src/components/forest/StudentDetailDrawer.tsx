"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { X, BarChart3, Target, User } from "lucide-react";
import { getStudentProfile, getStudentMastery } from "@/lib/api";
import { SvgTree } from "./trees/SvgTree";
import { getTreeColors } from "./trees/treeColors";
import { getEmotionLabel, getEmotionEmoji } from "./trees/useEmotionState";
import type { StudentTree } from "@/lib/types";
import { GROWTH_STAGES } from "@/lib/types";
import { OverviewTab } from "./drawer/OverviewTab";
import { TrajectoryTab } from "./drawer/TrajectoryTab";
import { ProfileTab } from "./drawer/ProfileTab";

function getStageLabel(stage: string): string {
  const found = GROWTH_STAGES.find((s) => s.key === stage);
  return found ? found.label : "播种";
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

  const masteryQuery = useQuery({
    queryKey: ["studentMastery", tree?.student_id],
    queryFn: () => getStudentMastery(tree!.student_id),
    enabled: !!tree?.student_id,
  });
  const masteryData = masteryQuery.data;

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
            transition={{ type: "spring", damping: 22, stiffness: 140 }}
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

            <div role="tablist" aria-label="学生详情标签" className="flex shrink-0 border-b border-parchment-300 bg-parchment-100/80">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const tabId = `tab-${tab.key}`;
                const panelId = `panel-${tab.key}`;
                return (
                  <button
                    key={tab.key}
                    role="tab"
                    id={tabId}
                    aria-selected={activeTab === tab.key}
                    aria-controls={panelId}
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
                  <div
                    key="panel-overview"
                    role="tabpanel"
                    id="panel-overview"
                    aria-labelledby="tab-overview"
                  >
                    <OverviewTab
                      tree={tree}
                      errorAccuracyMap={errorAccuracyMap}
                      totalDiagnoses={totalDiagnoses}
                      weakPoints={weakPoints}
                      studentInfo={studentInfo}
                      masteryData={masteryData}
                      lastWeek={lastWeek}
                      firstWeek={firstWeek}
                      overallTrend={overallTrend}
                    />
                  </div>
                )}

                {activeTab === "trajectory" && (
                  <div
                    key="panel-trajectory"
                    role="tabpanel"
                    id="panel-trajectory"
                    aria-labelledby="tab-trajectory"
                  >
                    <TrajectoryTab tree={tree} />
                  </div>
                )}

                {activeTab === "profile" && (
                  <div
                    key="panel-profile"
                    role="tabpanel"
                    id="panel-profile"
                    aria-labelledby="tab-profile"
                  >
                    <ProfileTab
                      tree={tree}
                      colors={colors}
                      overallTrend={overallTrend}
                      initialPersonalityTags={studentInfo?.personality_tags ?? []}
                      initialLearningStyle={studentInfo?.learning_style ?? ""}
                      initialNotes={studentInfo?.notes ?? ""}
                      initialGuidanceMode={studentInfo?.guidance_mode ?? "standard"}
                    />
                  </div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
