"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import type { HomeworkGenerateRequest, ExerciseType, DifficultyStrategy } from "@/lib/types";
import { EXERCISE_TYPES } from "@/lib/types";

const ERROR_CHIP_DATA = [
  { code: "E01", label: "基础事实", color: "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 data-[active=true]:bg-blue-600 data-[active=true]:text-white data-[active=true]:border-blue-600" },
  { code: "E02", label: "进位", color: "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 data-[active=true]:bg-amber-600 data-[active=true]:text-white data-[active=true]:border-amber-600" },
  { code: "E03", label: "退位", color: "bg-red-50 text-red-700 border-red-200 hover:bg-red-100 data-[active=true]:bg-red-600 data-[active=true]:text-white data-[active=true]:border-red-600" },
  { code: "E04", label: "数位对齐", color: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100 data-[active=true]:bg-purple-600 data-[active=true]:text-white data-[active=true]:border-purple-600" },
  { code: "E05", label: "运算顺序", color: "bg-teal-50 text-teal-700 border-teal-200 hover:bg-teal-100 data-[active=true]:bg-teal-600 data-[active=true]:text-white data-[active=true]:border-teal-600" },
  { code: "E06", label: "小数分数", color: "bg-cyan-50 text-cyan-700 border-cyan-200 hover:bg-cyan-100 data-[active=true]:bg-cyan-600 data-[active=true]:text-white data-[active=true]:border-cyan-600" },
  { code: "E07", label: "抄题转写", color: "bg-pink-50 text-pink-700 border-pink-200 hover:bg-pink-100 data-[active=true]:bg-pink-600 data-[active=true]:text-white data-[active=true]:border-pink-600" },
  { code: "E08", label: "步骤遗漏", color: "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100 data-[active=true]:bg-indigo-600 data-[active=true]:text-white data-[active=true]:border-indigo-600" },
  { code: "E09", label: "算理理解", color: "bg-lime-50 text-lime-700 border-lime-200 hover:bg-lime-100 data-[active=true]:bg-lime-600 data-[active=true]:text-white data-[active=true]:border-lime-600" },
  { code: "E10", label: "审题单位", color: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200 hover:bg-fuchsia-100 data-[active=true]:bg-fuchsia-600 data-[active=true]:text-white data-[active=true]:border-fuchsia-600" },
  { code: "E11", label: "未验算", color: "bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100 data-[active=true]:bg-orange-600 data-[active=true]:text-white data-[active=true]:border-orange-600" },
] as const;

const DIFFICULTY_OPTIONS: { value: DifficultyStrategy; label: string; desc: string }[] = [
  { value: "auto", label: "自适应", desc: "根据学生准确率自动分配" },
  { value: "A", label: "基础巩固", desc: "仅 A 级基础题" },
  { value: "B", label: "能力提升", desc: "仅 B 级中档题" },
  { value: "C", label: "六上挑战", desc: "分数、百分数、比和圆综合" },
  { value: "mixed", label: "高阶混合", desc: "B/C 为主，少量回扣基础" },
];

interface HomeworkFormProps {
  form: HomeworkGenerateRequest;
  onFormChange: (form: HomeworkGenerateRequest) => void;
  selectedExerciseTypes: ExerciseType[];
  onExerciseTypesChange: (types: ExerciseType[]) => void;
  difficultyStrategy: DifficultyStrategy;
  onDifficultyStrategyChange: (strategy: DifficultyStrategy) => void;
  onGenerate: () => void;
  loading: boolean;
  error: string | null;
  formError: string | null;
}

export function HomeworkForm({
  form,
  onFormChange,
  selectedExerciseTypes,
  onExerciseTypesChange,
  difficultyStrategy,
  onDifficultyStrategyChange,
  onGenerate,
  loading,
  error,
  formError,
}: HomeworkFormProps) {
  const [errorCodeError, setErrorCodeError] = useState<string | null>(null);

  function toggleErrorCode(code: string) {
    const current = form.error_codes_target ?? [];
    const next = current.includes(code)
      ? current.filter((c) => c !== code)
      : [...current, code];
    onFormChange({ ...form, error_codes_target: next });
    setErrorCodeError(null);
  }

  function toggleExerciseType(type: ExerciseType) {
    const next = selectedExerciseTypes.includes(type)
      ? selectedExerciseTypes.filter((t) => t !== type)
      : [...selectedExerciseTypes, type];
    onExerciseTypesChange(next);
  }

  function handleGenerateClick() {
    if (!form.error_codes_target || form.error_codes_target.length === 0) {
      setErrorCodeError("请至少选择一个错因类型");
      return;
    }
    if (!form.problem_count || form.problem_count < 1 || form.problem_count > 20) {
      setErrorCodeError("题目数量需在1-20之间");
      return;
    }
    setErrorCodeError(null);
    onGenerate();
  }

  return (
    <Card className="border-forest-200 bg-white text-foreground shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-forest-600" />
          六年级作业生成入口
        </CardTitle>
        <CardDescription className="text-muted-foreground">
          默认面向六上综合题：分数四则、百分数、比与圆，生成后必须由教师审核。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="classId">班级编号</Label>
            <Input
              id="classId"
              value={form.class_id}
              onChange={(e) => onFormChange({ ...form, class_id: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="studentId">学生编号</Label>
            <Input
              id="studentId"
              value={form.student_id ?? ""}
              onChange={(e) => onFormChange({ ...form, student_id: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="grade">年级</Label>
            <Input
              id="grade"
              type="number"
              min={1}
              max={6}
              value={form.grade}
              onChange={(e) => onFormChange({ ...form, grade: Number(e.target.value) })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="problemCount">题量</Label>
            <Input
              id="problemCount"
              type="number"
              min={1}
              max={20}
              value={form.problem_count ?? 4}
              onChange={(e) => onFormChange({ ...form, problem_count: Number(e.target.value) })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>目标错因</Label>
          <div className="flex flex-wrap gap-2">
            {ERROR_CHIP_DATA.map(({ code, label, color }) => {
              const active = (form.error_codes_target ?? []).includes(code);
              return (
                <button
                  key={code}
                  type="button"
                  data-active={active}
                  onClick={() => toggleErrorCode(code)}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all ${color}`}
                >
                  <span className="font-mono text-[10px] opacity-70">{code}</span>
                  {label}
                </button>
              );
            })}
          </div>
          {errorCodeError && <p className="text-sm text-amber-600">{errorCodeError}</p>}
        </div>

        <div className="space-y-2">
          <Label>题型范围</Label>
          <div className="flex flex-wrap gap-2">
            {EXERCISE_TYPES.map((type) => {
              const active = selectedExerciseTypes.includes(type);
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleExerciseType(type)}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-all ${
                    active
                      ? "border-forest-600 bg-forest-600 text-white"
                      : "border-forest-200 bg-forest-50 text-forest-700 hover:bg-forest-100"
                  }`}
                >
                  {type}
                </button>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground">
            已选 {selectedExerciseTypes.length} 种题型
          </p>
        </div>

        <div className="space-y-2">
          <Label>难度策略</Label>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {DIFFICULTY_OPTIONS.map(({ value, label, desc }) => (
              <button
                key={value}
                type="button"
                onClick={() => onDifficultyStrategyChange(value)}
                className={`rounded-lg border p-3 text-left transition-all ${
                  difficultyStrategy === value
                    ? "border-forest-600 bg-forest-50 ring-1 ring-forest-600"
                    : "border-forest-200 bg-white hover:border-forest-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex h-4 w-4 items-center justify-center rounded-full border-2 ${
                      difficultyStrategy === value
                        ? "border-forest-600 bg-forest-600"
                        : "border-forest-300"
                    }`}
                  >
                    {difficultyStrategy === value && (
                      <span className="block h-1.5 w-1.5 rounded-full bg-white" />
                    )}
                  </span>
                  <span className="text-sm font-medium text-foreground">{label}</span>
                </div>
                <p className="mt-1 pl-6 text-[11px] text-muted-foreground">{desc}</p>
              </button>
            ))}
          </div>
        </div>

        <Button
          onClick={handleGenerateClick}
          disabled={loading || !!formError}
          className="bg-orange-500 text-white hover:bg-orange-400"
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          生成个性化作业草案
        </Button>

        {formError && <p className="text-sm text-amber-600">{formError}</p>}
        {error && <p className="text-sm text-rose-500">{error}</p>}
      </CardContent>
    </Card>
  );
}
