"use client";

import { useMemo } from "react";
import type { WeeklyAccuracy, EmotionState } from "@/lib/types";

export function useEmotionState(weekly: WeeklyAccuracy[], overallAccuracy: number) {
  return useMemo(() => {
    if (!weekly || weekly.length < 2) {
      if (overallAccuracy >= 0.9) return { state: "thriving" as const, intensity: 0.8 };
      return { state: "stable" as const, intensity: 0 };
    }

    const recent = weekly.slice(-3);
    const accs = recent.map((w) => w.accuracy);
    const trend = accs[accs.length - 1] - accs[0];
    const latest = accs[accs.length - 1];

    if (overallAccuracy > 0.95 || (trend >= 0.10 && latest >= 0.70))
      return { state: "thriving" as const, intensity: Math.min(1, trend / 0.20) };
    if (trend > 0.05 && latest >= 0.70)
      return { state: "happy" as const, intensity: Math.min(1, trend / 0.15) };
    if (trend >= -0.05)
      return { state: "stable" as const, intensity: Math.abs(trend) / 0.10 };
    if (trend >= -0.15)
      return { state: "wilting" as const, intensity: Math.min(1, Math.abs(trend) / 0.15) };
    return { state: "struggling" as const, intensity: Math.min(1, Math.abs(trend) / 0.30) };
  }, [weekly, overallAccuracy]);
}

export function getEmotionLabel(state: EmotionState): string {
  const labels: Record<EmotionState, string> = {
    thriving: "蓬勃发展",
    happy: "开心成长",
    stable: "稳步前进",
    wilting: "需要加油",
    struggling: "需要关怀",
  };
  return labels[state];
}

export function getEmotionEmoji(state: EmotionState): string {
  const emojis: Record<EmotionState, string> = {
    thriving: "\u2728",
    happy: "\u{1F31F}",
    stable: "\u{1F331}",
    wilting: "\u{1F343}",
    struggling: "\u{1F327}",
  };
  return emojis[state];
}
