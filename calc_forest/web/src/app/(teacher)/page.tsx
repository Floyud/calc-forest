"use client";

import React, { useCallback, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  BookOpenCheck,
  ClipboardCheck,
  LayoutPanelTop,
  ShieldCheck,
  Sparkles,
  TreePine,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useClassForest, useClassSummary, useCurrentCycle } from "@/lib/api/hooks";
import { DEFAULT_CLASS_ID, DEFAULT_GRADE } from "@/lib/config";
import { ERROR_LABELS } from "@/lib/types";
import type { StudentTree } from "@/lib/types";
import { getEmotionSummary } from "@/lib/presentation";
import {
  ActionRail,
  HeroActionButton,
  InsightStrip,
  MetricCard,
  PageHero,
  SectionPanel,
  WorkspacePage,
} from "@/components/layout/workspace-shell";

const ClassErrorHeatmap = dynamic(
  () => import("@/components/forest/ClassErrorHeatmap").then((m) => ({ default: m.ClassErrorHeatmap })),
  { ssr: false },
);

const StudentDetailDrawer = dynamic(
  () => import("@/components/forest/StudentDetailDrawer").then((m) => ({ default: m.StudentDetailDrawer })),
  { ssr: false },
);

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") return "--";
  return `${Math.round(value * 100)}%`;
}

function StudentSummaryCard({
  tree,
  index,
  onClick,
}: {
  tree: StudentTree;
  index: number;
  onClick: (tree: StudentTree) => void;
}) {
  const accuracy = Math.round(tree.overall_accuracy * 100);
  const topError = tree.dominant_errors[0];
  const accuracyTone =
    accuracy >= 80
      ? "bg-emerald-500"
      : accuracy >= 60
        ? "bg-amber-500"
        : "bg-rose-500";

  return (
    <motion.button
      type="button"
      onClick={() => onClick(tree)}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="surface-panel text-left rounded-[22px] p-4 transition-transform hover:-translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.16em] text-[var(--tone-muted)]">重点关注</p>
          <p className="mt-2 text-lg font-medium text-[var(--tone-ink)]">{tree.student_name}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {tree.tree_species_name} · {getEmotionSummary(tree.emotional_state)}
          </p>
        </div>
        <span className="text-2xl">{tree.tree_species_emoji}</span>
      </div>
      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between text-xs text-[var(--tone-muted)]">
          <span>最近正确率</span>
          <span className="font-semibold text-[var(--tone-ink)]">{accuracy}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[var(--tone-soft)]">
          <div className={`h-full rounded-full ${accuracyTone}`} style={{ width: `${accuracy}%` }} />
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between gap-2">
        <Badge className="bg-white/78 text-[var(--tone-ink)] ring-1 ring-[color:var(--tone-line)]">
          {topError ? `${topError} ${ERROR_LABELS[topError as keyof typeof ERROR_LABELS] ?? ""}` : "表现稳定"}
        </Badge>
        <span className="text-xs text-[var(--tone-muted)]">查看详情</span>
      </div>
    </motion.button>
  );
}

export default function HomePage() {
  const { data: forest, isLoading: forestLoading, isError: forestError } = useClassForest(DEFAULT_CLASS_ID);
  const { data: summary } = useClassSummary(DEFAULT_CLASS_ID);
  const { data: cycle } = useCurrentCycle(DEFAULT_GRADE);
  const [selectedTree, setSelectedTree] = useState<StudentTree | null>(null);

  const handleCloseDrawer = useCallback(() => setSelectedTree(null), []);

  const quickStats = useMemo(() => [
    {
      label: "班级正确率",
      value: summary ? formatPercent(summary.class_accuracy) : forest ? formatPercent(forest.class_accuracy) : "--",
      note: "最近一轮练习的整体规则判题结果",
      icon: "📊",
      emphasis: "success" as const,
    },
    {
      label: "待关注学生",
      value: summary ? String(summary.students_needing_attention.length) : "--",
      note: "优先安排讲评、跟进或定向练习",
      icon: "👀",
      emphasis: "warm" as const,
    },
    {
      label: "当前周期",
      value: cycle ? `${cycle.academic_year} ${cycle.cycle_type}` : "--",
      note: "用于组织班级工作台上下文",
      icon: "🗓",
      emphasis: "default" as const,
    },
    {
      label: "班级人数",
      value: summary ? String(summary.total_students) : forest ? String(forest.trees.length) : "--",
      note: "当前已进入班级森林的学生数量",
      icon: "🌱",
      emphasis: "default" as const,
    },
  ], [cycle, forest, summary]);

  const topErrors =
    summary?.top_error_tags?.map((item) => `${item.code} ${ERROR_LABELS[item.code as keyof typeof ERROR_LABELS] ?? ""}`) ??
    forest?.class_top_errors.map((code) => `${code} ${ERROR_LABELS[code as keyof typeof ERROR_LABELS] ?? ""}`) ??
    [];

  const studentsNeedingAttention = useMemo(() => {
    if (!forest) return [];
    return [...forest.trees]
      .sort((a, b) => a.overall_accuracy - b.overall_accuracy)
      .slice(0, 6);
  }, [forest]);

  if (forestLoading) {
    return (
      <WorkspacePage>
        <div className="surface-hero h-56 animate-pulse rounded-[28px]" />
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="surface-panel h-36 animate-pulse rounded-[22px]" />
          ))}
        </div>
      </WorkspacePage>
    );
  }

  if (forestError || !forest) {
    return (
      <WorkspacePage>
        <SectionPanel title="班级数据暂不可用" description="请确认 FastAPI 后端服务正在运行。">
          <div className="flex flex-col items-center gap-4 rounded-[22px] border border-rose-200 bg-rose-50/80 px-6 py-10 text-center">
            <AlertCircle className="h-10 w-10 text-rose-500" />
            <div>
              <h2 className="text-lg font-semibold text-rose-700">无法连接后端服务</h2>
              <p className="mt-2 text-sm text-rose-600">后端服务暂不可用，请稍后重试。</p>
            </div>
          </div>
        </SectionPanel>
      </WorkspacePage>
    );
  }

  return (
    <WorkspacePage>
      <PageHero
        eyebrow="教师主导的错因诊断闭环"
        title="先看班级现在怎么样，再决定今天先做什么。"
        description="工作台把班级正确率、重点关注学生和下一步动作放到同一视图里。森林只作为成长隐喻存在，真正的主角是老师的判断与审核。"
        metric={{
          label: "班级当前氛围",
          value: getEmotionSummary(forest.class_emotional_state),
          note: `${forest.class_name} · ${forest.academic_year}`,
        }}
        actions={(
          <>
            <HeroActionButton href="/diagnose">
              进入诊断台
              <ArrowRight className="h-4 w-4" />
            </HeroActionButton>
            <HeroActionButton href="/classroom" variant="outline">
              打开课堂模式
              <LayoutPanelTop className="h-4 w-4" />
            </HeroActionButton>
            <HeroActionButton href="/homework" variant="outline">
              查看作业批阅
              <ClipboardCheck className="h-4 w-4" />
            </HeroActionButton>
          </>
        )}
        aside={(
          <div className="space-y-3">
            <InsightStrip
              title="高频错因"
              value={topErrors[0] ?? "暂无明显集中错因"}
              detail={topErrors[1] ? `其次为 ${topErrors[1]}` : "可继续观察最近练习的题型分布"}
              tone="warn"
            />
            <InsightStrip
              title="教师审核原则"
              value="所有 AI 批改与建议默认待教师确认"
              detail="系统先草拟，老师最后拍板，不绕过教师审核门。"
            />
            <InsightStrip
              title="今日建议"
              value={summary?.students_needing_attention.length ? `优先跟进 ${summary.students_needing_attention.length} 位学生` : "班级整体表现稳定"}
              detail="可先进行课堂讲评，再布置课后个性化练习。"
              tone="success"
            />
          </div>
        )}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickStats.map((item) => (
          <MetricCard
            key={item.label}
            label={item.label}
            value={item.value}
            note={item.note}
            icon={item.icon}
            emphasis={item.emphasis}
          />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionPanel
          title="班级森林总览"
          description="先聚焦需要老师优先处理的人，再深入单个学生详情。"
        >
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {studentsNeedingAttention.map((tree, index) => (
              <StudentSummaryCard key={tree.student_id} tree={tree} index={index} onClick={setSelectedTree} />
            ))}
          </div>
        </SectionPanel>

        <SectionPanel
          title="老师下一步可以做什么"
          description="围绕诊断、讲评、批阅三条主路径组织，不再把演示页和品牌页放在首要入口。"
        >
          <ActionRail
            title="主流程入口"
            items={[
              {
                href: "/diagnose",
                label: "逐题诊断",
                description: "录入题目与作答，查看规则证据、错因标签和讲解建议。",
                icon: <ShieldCheck className="h-4 w-4" />,
              },
              {
                href: "/classroom",
                label: "课堂讲评",
                description: "根据共性错因快速生成投屏练习，完成课中反馈。",
                icon: <LayoutPanelTop className="h-4 w-4" />,
              },
              {
                href: "/homework",
                label: "作业批阅",
                description: "生成作业、模拟识别、批改归档并完成教师审核。",
                icon: <ClipboardCheck className="h-4 w-4" />,
              },
            ]}
          />
          <div className="mt-4 grid gap-3">
            <InsightStrip
              title="品牌层"
              value="成长语气与树木百科已降级为辅助展示"
              detail="需要时再进入，不与教师主工作流竞争注意力。"
            />
            <div className="rounded-[18px] border border-[color:var(--tone-line)] bg-white/80 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-[var(--tone-ink)]">
                <Sparkles className="h-4 w-4 text-[var(--tone-accent)]" />
                演示时推荐顺序
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                工作台看概况 → 诊断台看单题 → 课堂模式看共性讲评 → 作业批阅看教师审核闭环。
              </p>
            </div>
          </div>
        </SectionPanel>
      </section>

      <SectionPanel
        title="班级错因热力图"
        description="森林是表达层，真正的分析仍然落在错因分布与学生个体差异上。"
      >
        <ClassErrorHeatmap trees={forest.trees} onStudentClick={setSelectedTree} />
      </SectionPanel>

      <SectionPanel
        title="低压力陪伴入口"
        description="这些页面继续保留，但不再占据教师首页核心位置。"
      >
        <div className="grid gap-3 md:grid-cols-3">
          {[
            {
              href: "/guidance",
              label: "引导预览",
              description: "查看如何一步步引导孩子理解错因，而不是直接给答案。",
              icon: <BookOpenCheck className="h-4 w-4" />,
            },
            {
              href: "/forest",
              label: "成长轨迹",
              description: "回看学生成长和班级森林表达，不把它当主入口。",
              icon: <TreePine className="h-4 w-4" />,
            },
            {
              href: "/botanical",
              label: "树木百科",
              description: "作为品牌表达与课堂温度补充，不反向主导工作台风格。",
              icon: <Sparkles className="h-4 w-4" />,
            },
          ].map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-[20px] border border-[color:var(--tone-line)] bg-white/80 p-4 transition-all hover:-translate-y-0.5 hover:bg-white"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-[var(--tone-soft)] text-[var(--tone-accent-strong)]">
                {item.icon}
              </div>
              <h3 className="mt-4 text-base font-medium text-[var(--tone-ink)]">{item.label}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
            </a>
          ))}
        </div>
      </SectionPanel>

      <AnimatePresence>
        {selectedTree && (
          <StudentDetailDrawer
            tree={selectedTree}
            onClose={handleCloseDrawer}
          />
        )}
      </AnimatePresence>
    </WorkspacePage>
  );
}
