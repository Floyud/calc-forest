"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import type { StudentTree } from "@/lib/types";
import { ERROR_LABELS } from "@/lib/types";

interface TrajectoryTabProps {
  tree: StudentTree;
}

export function TrajectoryTab({ tree }: TrajectoryTabProps) {
  const errorDistribution = useMemo(() => {
    return tree.dominant_errors.map((code) => ({
      code,
      label: ERROR_LABELS[code as keyof typeof ERROR_LABELS] ?? code,
      severity: code === "E99" ? "low" : ("medium" as const),
    }));
  }, [tree]);

  return (
    <motion.div
      key="trajectory"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      className="space-y-4"
    >
      <h3 className="text-sm font-medium text-ink-500">错因时间线</h3>
      {errorDistribution.length > 0 ? (
        <div className="space-y-3">
          {errorDistribution.map((err, i) => (
            <div key={err.code} className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warm-100 text-xs font-bold text-warm-500">
                {i + 1}
              </div>
              <div className="flex-1 rounded-lg border border-parchment-300 bg-white p-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-volcano-300 text-volcano-500 text-xs">
                    {err.code}
                  </Badge>
                  <span className="text-sm font-medium text-ink-500">{err.label}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  需要通过针对性练习巩固此知识点
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-parchment-300 bg-white p-6 text-center">
          <p className="text-sm text-muted-foreground">暂无错因记录</p>
        </div>
      )}

      <h3 className="pt-2 text-sm font-medium text-ink-500">周度准确率走势</h3>
      <div className="space-y-2">
        {tree.weekly_accuracy.map((w) => (
          <div key={w.week_number} className="flex items-center gap-3">
            <span className="w-8 text-xs text-muted-foreground">W{w.week_number}</span>
            <div className="relative h-4 flex-1 overflow-hidden rounded-full bg-parchment-200">
              <motion.div
                className="absolute left-0 top-0 h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${w.accuracy * 100}%` }}
                transition={{ delay: 0.1, duration: 0.6 }}
                style={{
                  backgroundColor: w.accuracy >= 0.8 ? "#46803c" : w.accuracy >= 0.6 ? "#d4a843" : "#e8945a",
                }}
              />
            </div>
            <span className="w-10 text-right text-xs font-medium text-ink-400">
              {Math.round(w.accuracy * 100)}%
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
