"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, Circle, AlertTriangle } from "lucide-react";
import type { DifySessionDraftResponse, DifySessionDraftRequest } from "@/lib/types";

type NodeStatus = "pending" | "running" | "complete" | "skipped" | "failed";

interface PipelineNode {
  name: string;
  label: string;
  status: NodeStatus;
  message: string;
  duration_ms: number;
  summary: Record<string, string | number | boolean | null>;
}

interface PipelineProgressProps {
  request: DifySessionDraftRequest;
  onComplete: (result: DifySessionDraftResponse) => void;
  onError: (error: string) => void;
}

const NODE_ORDER = [
  { name: "diagnosis", label: "错因诊断", icon: "🔍" },
  { name: "teacher_summary", label: "AI 摘要", icon: "🤖" },
  { name: "practice", label: "练习推荐", icon: "📝" },
  { name: "growth_config", label: "成长配置", icon: "🌳" },
  { name: "profile_update", label: "更新画像", icon: "📊" },
  { name: "growth_update", label: "更新成长", icon: "🌱" },
];

function buildInitialNodes(): PipelineNode[] {
  return NODE_ORDER.map((n) => ({
    name: n.name,
    label: n.label,
    status: "pending" as NodeStatus,
    message: "",
    duration_ms: 0,
    summary: {},
  }));
}

export default function PipelineProgress({
  request,
  onComplete,
  onError,
}: PipelineProgressProps) {
  const [nodes, setNodes] = useState<PipelineNode[]>(buildInitialNodes);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pipelineDone, setPipelineDone] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const updateNode = useCallback(
    (name: string, patch: Partial<PipelineNode>) => {
      setNodes((prev) =>
        prev.map((n) => (n.name === name ? { ...n, ...patch } : n)),
      );
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;

    const API_BASE =
      process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

    fetch(`${API_BASE}/api/dify/pipeline-stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error("No readable stream");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            if (!part.trim()) continue;

            let eventType = "";
            let dataStr = "";

            for (const line of part.split("\n")) {
              if (line.startsWith("event: ")) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith("data: ")) {
                dataStr = line.slice(6);
              }
            }

            if (!dataStr) continue;

            let data: Record<string, unknown>;
            try {
              data = JSON.parse(dataStr);
            } catch {
              continue;
            }

            switch (eventType) {
              case "node_progress": {
                const nodeName = data.node as string;
                updateNode(nodeName, {
                  status: "running",
                  message: (data.message as string) ?? "",
                });
                break;
              }
              case "node_complete": {
                const nodeName = data.node as string;
                const status = (data.status as string) ?? "complete";
                updateNode(nodeName, {
                  status: status === "failed" ? "failed" : status === "skipped" ? "skipped" : "complete",
                  duration_ms: (data.duration_ms as number) ?? 0,
                  summary: data as Record<string, string | number | boolean | null>,
                });
                break;
              }
              case "done": {
                const result = data.result as DifySessionDraftResponse;
                if (result) {
                  onComplete(result);
                }
                setPipelineDone(true);
                break;
              }
              case "error": {
                const msg = (data.message as string) ?? (data.error as string) ?? "未知错误";
                setErrorMsg(msg);
                onError(msg);
                break;
              }
            }
          }
        }
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        const msg = err instanceof Error ? err.message : "连接失败";
        setErrorMsg(msg);
        onError(msg);
      });

    return () => {
      controller.abort();
    };
  }, [request, updateNode, onComplete, onError]);

  const currentRunningNode = nodes.find((n) => n.status === "running");
  const headerText = pipelineDone
    ? "诊断完成"
    : errorMsg
      ? "诊断出错"
      : currentRunningNode
        ? `${currentRunningNode.label}中...`
        : "AI 诊断流水线";

  return (
    <div className="rounded-xl border border-forest-200 bg-forest-50/30 p-4">
      <div className="mb-3 flex items-center gap-2">
        {pipelineDone ? (
          <Check className="h-4 w-4 text-forest-600" />
        ) : (
          <Loader2 className="h-4 w-4 animate-spin text-forest-600" />
        )}
        <span className="text-sm font-medium text-forest-700">
          {headerText}
        </span>
      </div>

      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {nodes.map((node, i) => {
          const meta = NODE_ORDER.find((n) => n.name === node.name);
          return (
            <div key={node.name} className="flex items-start">
              <div className="flex flex-col items-center" style={{ minWidth: 90 }}>
                <div className="relative">
                  <motion.div
                    className={`flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm ${
                      node.status === "complete"
                        ? "border-forest-500 bg-forest-500 text-white"
                        : node.status === "running"
                          ? "border-forest-400 bg-forest-100 text-forest-600"
                          : node.status === "failed"
                            ? "border-red-400 bg-red-50 text-red-500"
                            : node.status === "skipped"
                              ? "border-gray-300 bg-gray-50 text-gray-400"
                              : "border-gray-200 bg-gray-50 text-gray-300"
                    }`}
                    animate={
                      node.status === "running"
                        ? { scale: [1, 1.1, 1] }
                        : { scale: 1 }
                    }
                    transition={
                      node.status === "running"
                        ? { repeat: Infinity, duration: 1.2 }
                        : { duration: 0.2 }
                    }
                  >
                    {node.status === "complete" ? (
                      <Check className="h-4 w-4" />
                    ) : node.status === "running" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : node.status === "failed" ? (
                      <AlertTriangle className="h-4 w-4" />
                    ) : node.status === "skipped" ? (
                      <span className="text-xs">—</span>
                    ) : (
                      <Circle className="h-3 w-3" />
                    )}
                  </motion.div>
                </div>

                <span
                  className={`mt-1 text-center text-xs font-medium leading-tight ${
                    node.status === "pending" ? "text-gray-400" : "text-gray-700"
                  }`}
                >
                  {meta?.icon} {node.label}
                </span>

                <AnimatePresence>
                  {node.status === "complete" && node.duration_ms > 0 && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-[10px] text-forest-500"
                    >
                      {node.duration_ms}ms
                    </motion.span>
                  )}
                  {node.status === "running" && node.message && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="max-w-[90px] text-center text-[10px] leading-tight text-forest-600"
                    >
                      {node.message}
                    </motion.span>
                  )}
                </AnimatePresence>

                {node.name === "diagnosis" &&
                  node.status === "complete" &&
                  node.summary.error_code && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-1 flex flex-col items-center gap-0.5"
                    >
                      <span className="rounded bg-fruit-500/90 px-1.5 py-0.5 text-[10px] font-bold text-white">
                        {node.summary.error_code as string}
                      </span>
                      <span className="text-[9px] text-gray-500">
                        {node.summary.is_correct
                          ? "正确"
                          : `${Math.round(((node.summary.confidence as number) ?? 0) * 100)}%`}
                      </span>
                    </motion.div>
                  )}

                {node.name === "practice" &&
                  node.status === "complete" &&
                  node.summary.practice_count != null && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mt-1 rounded bg-warm-400/80 px-1.5 py-0.5 text-[10px] text-white"
                    >
                      {node.summary.practice_count as number} 道题
                    </motion.span>
                  )}

                {node.name === "growth_update" &&
                  node.status === "complete" &&
                  node.summary.current_stage && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mt-1 rounded bg-forest-400/80 px-1.5 py-0.5 text-[10px] text-white"
                    >
                      {node.summary.current_stage as string}
                    </motion.span>
                  )}
              </div>

              {i < nodes.length - 1 && (
                <div className="mt-4 flex items-center">
                  <div
                    className={`h-0.5 w-5 transition-colors duration-300 ${
                      node.status === "complete"
                        ? "bg-forest-400"
                        : "bg-gray-200"
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <AnimatePresence>
        {errorMsg && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 flex items-center gap-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-600"
          >
            <AlertTriangle className="h-3 w-3 shrink-0" />
            {errorMsg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
