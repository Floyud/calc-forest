import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  CalendarClock,
  ClipboardCheck,
  LayoutPanelTop,
  Leaf,
  ShieldCheck,
  TreePine,
} from "lucide-react";
import { getEmotionEmoji, getEmotionLabel } from "@/components/forest/trees/useEmotionState";

export interface NavItem {
  href: string;
  label: string;
  shortLabel?: string;
  description: string;
  icon: LucideIcon;
}

export const PRIMARY_NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "工作台",
    description: "班级总览、待办与重点关注对象",
    icon: TreePine,
  },
  {
    href: "/classroom",
    label: "课堂模式",
    description: "根据共性错因生成随堂练习与大屏反馈",
    icon: LayoutPanelTop,
  },
  {
    href: "/homework",
    label: "作业批阅",
    shortLabel: "作业闭环",
    description: "作业生成、识别、批改与教师审核",
    icon: ClipboardCheck,
  },
  {
    href: "/schedule",
    label: "课表排课",
    description: "管理每周数学课时段，自动或手动布置作业",
    icon: CalendarClock,
  },
  {
    href: "/diagnose",
    label: "诊断台",
    description: "逐题诊断、错因证据与练习建议",
    icon: ShieldCheck,
  },
];

export const SECONDARY_NAV_ITEMS: NavItem[] = [
  {
    href: "/guidance",
    label: "引导预览",
    description: "查看不直接给答案的引导话术",
    icon: BookOpen,
  },
  {
    href: "/forest",
    label: "成长语气",
    description: "查看成长轨迹与反馈风格",
    icon: TreePine,
  },
  {
    href: "/botanical",
    label: "树木百科",
    description: "教师端品牌表达与树种知识卡片",
    icon: Leaf,
  },
];

export const DEMO_STEPS = [
  {
    href: "/",
    label: "班级工作台",
    description: "先看班级整体状态、重点学生与下一步动作。",
    emoji: "🌲",
  },
  {
    href: "/diagnose",
    label: "错因诊断",
    description: "录入一条作答，查看规则诊断、证据和建议。",
    emoji: "🔍",
  },
  {
    href: "/classroom",
    label: "课堂模式",
    description: "根据班级共性错因生成随堂练习并投屏讲评。",
    emoji: "📋",
  },
  {
    href: "/homework",
    label: "作业批阅",
    description: "完成作业生成、识别、批改和教师审核闭环。",
    emoji: "📝",
  },
  {
    href: "/forest",
    label: "成长轨迹",
    description: "回看学生成长记录与班级森林表达层。",
    emoji: "📈",
  },
];

export function getStatusTone(status: string): string {
  if (["archived", "graded", "recognized", "completed", "reviewed"].includes(status)) {
    return "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
  }
  if (["processing", "queued", "submitted", "in_progress", "assigned"].includes(status)) {
    return "bg-amber-50 text-amber-700 ring-1 ring-amber-200";
  }
  if (["pending_teacher_review", "pending"].includes(status)) {
    return "bg-sky-50 text-sky-700 ring-1 ring-sky-200";
  }
  return "bg-[var(--tone-soft)] text-[var(--tone-ink)] ring-1 ring-[color:var(--tone-line)]";
}

export function getReviewTone(reviewStatus: string): string {
  return reviewStatus === "pending_teacher_review" || reviewStatus === "pending"
    ? "bg-sky-50 text-sky-700 ring-1 ring-sky-200"
    : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200";
}

export function getEmotionSummary(emotion: Parameters<typeof getEmotionLabel>[0]) {
  return `${getEmotionEmoji(emotion)} ${getEmotionLabel(emotion)}`;
}
