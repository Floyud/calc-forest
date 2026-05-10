"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  Flame,
  LayoutPanelTop,
  TreePine,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useClassForest,
  useClassSummary,
  useStudentProfile,
  useCurrentCycle,
} from "@/lib/api/hooks";
import { DEFAULT_CLASS_ID, DEFAULT_STUDENT_ID, DEFAULT_GRADE } from "@/lib/config";
import { getEmotionLabel } from "@/components/forest/trees/useEmotionState";

const ClassErrorHeatmap = dynamic(
  () => import("@/components/forest/ClassErrorHeatmap").then((m) => ({ default: m.ClassErrorHeatmap })),
  { ssr: false },
);

function formatPercent(value: number | null | undefined) {
  if (typeof value !== "number") return "--";
  return `${Math.round(value * 100)}%`;
}

export default function HomePage() {
  const { data: forest, isLoading: forestLoading, isError: forestError } = useClassForest(DEFAULT_CLASS_ID);
  const { data: summary } = useClassSummary(DEFAULT_CLASS_ID);
  const { data: cycle } = useCurrentCycle(DEFAULT_GRADE);
  const { data: profile } = useStudentProfile(DEFAULT_STUDENT_ID);

  const loading = forestLoading;

  const quickStats = [
    {
      label: "班级正确率",
      value: summary ? formatPercent(summary.class_accuracy) : forest ? formatPercent(forest.class_accuracy) : "--",
      note: "最近练习的整体表现",
      icon: "📊",
    },
    {
      label: "需关注学生",
      value: summary ? String(summary.students_needing_attention.length) : "--",
      note: "优先安排讲评或专项练习",
      icon: "👀",
    },
    {
      label: "当前周期",
      value: cycle ? `${cycle.academic_year} ${cycle.cycle_type}` : "--",
      note: "正在进行的学期",
      icon: "📅",
    },
    {
      label: "学生画像",
      value: profile ? formatPercent(profile.accuracy) : "--",
      note: "单个学生的准确率参考",
      icon: "🌱",
    },
  ];

  const topErrors =
    summary?.top_error_tags?.map((item) => `${item.code}:${item.count}`) ??
    forest?.class_top_errors.map((code) => `${code}`) ??
    [];

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="space-y-4">
          <div className="h-6 w-56 animate-pulse rounded bg-muted" />
          <div className="h-24 animate-pulse rounded-xl bg-forest-100" />
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-28 animate-pulse rounded-xl bg-forest-100" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (forestError || !forest) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50/50 p-10 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-red-700">无法连接后端服务</h2>
          <p className="text-sm text-red-600">
            请确认 FastAPI 后端正在运行（http://127.0.0.1:8000）
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:py-10">
      <section className="relative overflow-hidden rounded-xl border border-forest-200 bg-gradient-to-br from-forest-50 via-white to-warm-50 p-8 shadow-lg shadow-forest-200/30 md:p-12">
        <div className="absolute inset-x-0 top-0 h-px bg-forest-300/30" />
        <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-warm-200/25 blur-3xl" />
        <div className="absolute -bottom-8 left-1/4 h-32 w-32 rounded-full bg-forest-200/20 blur-3xl" />

        <div className="relative space-y-6">
          <Badge className="bg-forest-100 text-forest-700">教师端</Badge>

          <div className="space-y-3">
            <h1 className="max-w-3xl text-3xl font-semibold tracking-normal text-forest-800 md:text-5xl">
              我的计算森林
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
              帮助老师了解每位学生的计算掌握情况，诊断错因、生成练习、跟踪成长。每一棵小树，都记录着孩子的进步。
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link href="/diagnose">
              <Button className="bg-orange-500 text-white hover:bg-orange-400">
                进入诊断台
                <ArrowRight className="ml-1" />
              </Button>
            </Link>
            <Link href="/classroom">
              <Button
                variant="outline"
                className="border-forest-300 text-forest-700 hover:bg-forest-50"
              >
                打开课堂模式
                <LayoutPanelTop className="ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickStats.map((item) => (
          <Card key={item.label} className="border-forest-200 bg-white text-foreground shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-muted-foreground">
                <span className="mr-1">{item.icon}</span>
                {item.label}
              </CardDescription>
              <CardTitle className="text-xl text-foreground">{item.value}</CardTitle>
            </CardHeader>
            <CardContent className="pt-0 text-xs text-muted-foreground">{item.note}</CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Flame className="h-4 w-4 text-warm-400" />
              快速入口
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              点击进入常用功能
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            <Link
              href="/diagnose"
              className="rounded-lg border border-forest-100 bg-forest-50/30 p-4 transition-colors hover:bg-forest-50"
            >
              <ClipboardCheck className="h-5 w-5 text-warm-400" />
              <h3 className="mt-3 text-sm font-medium text-foreground">错因诊断</h3>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                录入题目和学生作答，智能分析错因并推荐针对性练习。
              </p>
            </Link>
            <Link
              href="/classroom"
              className="rounded-lg border border-forest-100 bg-forest-50/30 p-4 transition-colors hover:bg-forest-50"
            >
              <LayoutPanelTop className="h-5 w-5 text-forest-500" />
              <h3 className="mt-3 text-sm font-medium text-foreground">课堂模式</h3>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                从班级高频错因快速生成投屏练习，现场记录掌握情况。
              </p>
            </Link>
            <Link
              href="/homework"
              className="rounded-lg border border-forest-100 bg-forest-50/30 p-4 transition-colors hover:bg-forest-50"
            >
              <BookOpen className="h-5 w-5 text-forest-600" />
              <h3 className="mt-3 text-sm font-medium text-foreground">作业管理</h3>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                自动生成差异化作业，按学生错因分配不同难度练习。
              </p>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <TreePine className="h-4 w-4 text-forest-500" />
              班级概况
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              查看班级整体情况和成长记录
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-forest-100 bg-forest-50/30 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground/75">{forest.class_name}</span>
                <Badge variant="outline" className="border-forest-200 text-forest-600">
                  {forest.academic_year}
                </Badge>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">班级氛围</p>
                  <p className="mt-1 text-foreground">{getEmotionLabel(forest.class_emotional_state)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">学生人数</p>
                  <p className="mt-1 text-foreground">{forest.trees.length}</p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-forest-100 bg-forest-50/30 p-4">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">高频错因</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {topErrors.map((item) => (
                  <Badge key={item} variant="outline" className="border-warm-200 text-warm-600">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>

            <Link
              href="/forest"
              className="flex items-center gap-2 rounded-lg border border-forest-100 bg-forest-50/30 p-4 transition-colors hover:bg-forest-50"
            >
              <TreePine className="h-4 w-4 text-forest-400" />
              <span className="text-sm text-foreground/80">查看班级森林</span>
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="mt-8">
        <Card className="border-forest-200 bg-white text-foreground shadow-sm">
          <CardContent className="p-6">
            <ClassErrorHeatmap trees={forest.trees} />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
