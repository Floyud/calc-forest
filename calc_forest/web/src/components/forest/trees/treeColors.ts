import type { EmotionState } from "@/lib/types";

export type CanopyType = "cloud" | "round" | "oval" | "star" | "triangle" | "spreading";

export interface TreeColorConfig {
  trunk: string;
  trunkDark: string;
  trunkLight: string;
  leaf: string;
  leafDark: string;
  leafLight: string;
  flower: string;
  fruit: string;
  ground: string;
  groundDark: string;
  sky: string;
  skyDark: string;
  particle: string;
  glow: string;
  saturation: number;
  outline: string;
  outlineAlt: string;
  canopyType: CanopyType;
}

const OUTLINE = "rgba(60,40,20,0.25)";
const OUTLINE_ALT = "rgba(60,40,20,0.15)";

const BASE_COLORS: Record<string, Partial<TreeColorConfig> & { canopyType: CanopyType }> = {
  cherry: { flower: "#FFB7D5", fruit: "#FF7EB3", canopyType: "cloud" },
  apple: { flower: "#FFE0E6", fruit: "#FF6B6B", canopyType: "round" },
  orange: { flower: "#FFF0D9", fruit: "#FFA940", canopyType: "oval" },
  maple: { flower: "#FFF5CC", fruit: "#FFD700", canopyType: "star" },
  pine: { flower: "#D4EDDA", fruit: "#66BB6A", canopyType: "triangle" },
  oak: { flower: "#E8DDD4", fruit: "#A0785A", canopyType: "spreading" },
};

const EMOTION_MODIFIERS: Record<EmotionState, Partial<TreeColorConfig> & { saturation: number }> = {
  thriving: {
    leaf: "#4ADE80",
    leafDark: "#22C55E",
    leafLight: "#86EFAC",
    trunk: "#8B5E3C",
    trunkDark: "#6B4226",
    trunkLight: "#A97B50",
    ground: "#86EFAC",
    groundDark: "#4ADE80",
    sky: "#FFF8E1",
    skyDark: "#FFECB3",
    particle: "#FACC15",
    glow: "rgba(255,213,79,0.35)",
    saturation: 1.3,
  },
  happy: {
    leaf: "#22C55E",
    leafDark: "#16A34A",
    leafLight: "#6EE7B7",
    trunk: "#8B5E3C",
    trunkDark: "#6B4226",
    trunkLight: "#A97B50",
    ground: "#A7F3D0",
    groundDark: "#6EE7B7",
    sky: "#ECFDF5",
    skyDark: "#D1FAE5",
    particle: "#FDE68A",
    glow: "rgba(255,213,79,0.18)",
    saturation: 1.1,
  },
  stable: {
    leaf: "#34D399",
    leafDark: "#10B981",
    leafLight: "#6EE7B7",
    trunk: "#8B5E3C",
    trunkDark: "#6B4226",
    trunkLight: "#A97B50",
    ground: "#A7F3D0",
    groundDark: "#6EE7B7",
    sky: "#F0FDF4",
    skyDark: "#DCFCE7",
    particle: "#86EFAC",
    glow: "transparent",
    saturation: 1.0,
  },
  wilting: {
    leaf: "#BEF264",
    leafDark: "#A3E635",
    leafLight: "#D9F99D",
    trunk: "#8B5E3C",
    trunkDark: "#6B4226",
    trunkLight: "#A97B50",
    ground: "#ECFCCB",
    groundDark: "#D9F99D",
    sky: "#FEFCE8",
    skyDark: "#FEF9C3",
    particle: "#D4A76A",
    glow: "transparent",
    saturation: 0.75,
  },
  struggling: {
    leaf: "#D4A76A",
    leafDark: "#C4956A",
    leafLight: "#E8C99B",
    trunk: "#8B5E3C",
    trunkDark: "#6B4226",
    trunkLight: "#A97B50",
    ground: "#FDE68A",
    groundDark: "#FCD34D",
    sky: "#FFFBEB",
    skyDark: "#FEF3C7",
    particle: "#D4A76A",
    glow: "transparent",
    saturation: 0.5,
  },
};

export function getTreeColors(
  species: string,
  emotion: EmotionState,
  intensity: number = 0,
): TreeColorConfig {
  void intensity;
  const base = BASE_COLORS[species] || BASE_COLORS.cherry;
  const mod = EMOTION_MODIFIERS[emotion];

  return {
    trunk: mod.trunk || "#8B5E3C",
    trunkDark: mod.trunkDark || "#6B4226",
    trunkLight: mod.trunkLight || "#A97B50",
    leaf: mod.leaf || "#34D399",
    leafDark: mod.leafDark || "#10B981",
    leafLight: mod.leafLight || "#6EE7B7",
    flower: base.flower || "#FFB7D5",
    fruit: base.fruit || "#FF7EB3",
    ground: mod.ground || "#A7F3D0",
    groundDark: mod.groundDark || "#6EE7B7",
    sky: mod.sky || "#F0FDF4",
    skyDark: mod.skyDark || "#DCFCE7",
    particle: mod.particle || "#86EFAC",
    glow: mod.glow || "transparent",
    saturation: mod.saturation,
    outline: OUTLINE,
    outlineAlt: OUTLINE_ALT,
    canopyType: base.canopyType,
  };
}

export const STAGE_SIZES: Record<string, { width: number; height: number; trunkH: number; crownR: number }> = {
  seed: { width: 60, height: 80, trunkH: 0, crownR: 0 },
  sprout: { width: 60, height: 90, trunkH: 15, crownR: 8 },
  first_leaf: { width: 70, height: 100, trunkH: 25, crownR: 14 },
  taller: { width: 80, height: 110, trunkH: 35, crownR: 20 },
  branching: { width: 90, height: 120, trunkH: 40, crownR: 28 },
  sturdy: { width: 100, height: 130, trunkH: 45, crownR: 35 },
  bud: { width: 110, height: 140, trunkH: 50, crownR: 40 },
  flowering: { width: 120, height: 150, trunkH: 52, crownR: 45 },
  mature: { width: 130, height: 160, trunkH: 55, crownR: 50 },
};
