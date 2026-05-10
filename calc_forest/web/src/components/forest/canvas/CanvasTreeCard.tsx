"use client";

import { useRef, useEffect, useMemo, useState } from "react";
import type { EmotionState } from "@/lib/types";
import type { TreeColorConfig } from "../trees/treeColors";
import { STAGE_SIZES } from "../trees/treeColors";
import { renderTree } from "./CanvasTreeRenderer";
import { ParticleSystem } from "./CanvasParticleSystem";

interface CanvasTreeProps {
  stage: string;
  emotion: EmotionState;
  colors: TreeColorConfig;
  speciesId?: string;
  size?: number;
  animate?: boolean;
  index?: number;
  onError?: () => void;
}

export function CanvasTree({
  stage,
  emotion,
  colors,
  size,
  animate = true,
  index = 0,
  onError,
}: CanvasTreeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef(0);
  const mountRef = useRef(0);
  const particleRef = useRef<ParticleSystem | null>(null);
  const lastRef = useRef(0);
  const mouseRef = useRef({ x: 0, y: 0 });
  const [canvasFailed, setCanvasFailed] = useState(false);

  const { dw, dh } = useMemo(() => {
    const cfg = STAGE_SIZES[stage] ?? STAGE_SIZES.seed;
    const w = size ?? cfg.width;
    const h = size ? size * (cfg.height / cfg.width) : cfg.height;
    return { dw: w, dh: h };
  }, [stage, size]);

  useEffect(() => {
    if (canvasFailed) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    try {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = dw * dpr;
    canvas.height = dh * dpr;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setCanvasFailed(true);
      onError?.();
      return;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const mt = performance.now();
    mountRef.current = mt;

    const cfg = STAGE_SIZES[stage] ?? STAGE_SIZES.seed;
    const sc = dw / cfg.width;
    const trunkH = cfg.trunkH * sc;
    const crownR = cfg.crownR * sc;
    const baseY = dh - 10;
    const crownCy = baseY - trunkH - crownR * 0.4;

    if (animate && emotion !== "stable") {
      particleRef.current = new ParticleSystem(emotion, {
        cx: dw / 2,
        cy: crownCy,
        width: dw,
        height: dh,
        color: colors.particle,
        intensity: 1,
      });
    } else {
      particleRef.current = null;
    }

    if (!animate) {
      ctx.clearRect(0, 0, dw, dh);
      renderTree(ctx, { stage, emotion, colors, size, time: mt, mountTime: mt });
      return;
    }

    const loop = (now: number) => {
      const dt = lastRef.current ? (now - lastRef.current) / 1000 : 1 / 60;
      lastRef.current = now;

      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, dw, dh);

      const px = mouseRef.current.x;
      const py = mouseRef.current.y;
      ctx.translate(px, py);

      renderTree(ctx, { stage, emotion, colors, size, time: now, mountTime: mt });

      const ps = particleRef.current;
      if (ps) {
        ps.update(Math.min(dt, 0.1));
        ps.render(ctx, now);
      }

      ctx.restore();
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    } catch {
      setCanvasFailed(true);
      onError?.();
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [stage, emotion, colors, size, animate, dw, dh, canvasFailed, onError]);

  useEffect(() => {
    if (!animate) return;
    const onMove = (e: MouseEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = (e.clientX - cx) / window.innerWidth;
      const dy = (e.clientY - cy) / window.innerHeight;
      const f = 0.5 + index * 0.15;
      mouseRef.current = { x: dx * f, y: dy * f };
    };
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMove);
  }, [animate, index]);

  if (canvasFailed) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{ width: dw, height: dh, display: "block" }}
    />
  );
}
