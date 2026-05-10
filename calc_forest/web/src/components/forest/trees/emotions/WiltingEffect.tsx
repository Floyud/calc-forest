"use client";

import { useMemo } from "react";

interface ParticleProps {
  cx: number;
  cy: number;
  width: number;
  height: number;
  color: string;
}

function DroopingBud({ x, y, delay }: { x: number; y: number; delay: number }) {
  return (
    <svg
      className="absolute"
      style={{
        left: x - 5,
        top: y - 4,
        width: 10,
        height: 12,
        animation: `bug-crawl 6s ${delay}s infinite ease-in-out`,
      }}
      viewBox="0 0 10 12"
    >
      <defs>
        <linearGradient id={`bud-stem-${delay}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6B8E23" />
          <stop offset="100%" stopColor="#8B7355" />
        </linearGradient>
      </defs>
      <path d="M5,12 C5,10 4,7 3,5" stroke="#6B8E23" strokeWidth="0.8" fill="none" strokeLinecap="round" />
      <ellipse cx="3" cy="3.5" rx="2.8" ry="3.5" fill="#D4A76A" opacity={0.8} />
      <ellipse cx="2" cy="3" rx="1.5" ry="2.5" fill="#C4956A" opacity={0.5} />
      <ellipse cx="2" cy="2" rx="0.8" ry="1.2" fill="rgba(255,255,255,0.15)" />
    </svg>
  );
}

export function WiltingEffect({ cx, cy, width, height, color }: ParticleProps) {
  void height;
  const leafColors = ["#E8A840", "#D4843A", "#C47232", "#B8922A"];

  const leaves = useMemo(() => {
    return Array.from({ length: 4 }, (_, i) => ({
      id: i,
      startX: cx + (Math.random() - 0.5) * width * 0.4,
      startY: cy + Math.random() * 10,
      driftX: (Math.random() - 0.5) * 20,
      delay: 2 + Math.random() * 5,
      duration: 3 + Math.random() * 2,
      rotation: Math.random() * 360,
      color: leafColors[i % leafColors.length],
    }));
  }, [cx, cy, width]);

  const buds = useMemo(() => {
    return Array.from({ length: 2 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.3,
      y: cy - 5 + Math.random() * 10,
      delay: i * 2.5,
    }));
  }, [cx, cy, width]);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {leaves.map((l) => (
        <div
          key={l.id}
          className="absolute"
          style={{
            left: l.startX - 4,
            top: l.startY,
            width: 9,
            height: 7,
            borderRadius: "50% 10% 50% 10%",
            backgroundColor: l.color,
            opacity: 0.7,
            animation: `leaf-fall ${l.duration}s ${l.delay}s infinite ease-in-out`,
            "--drift-x": `${l.driftX}px`,
            "--rotation": `${l.rotation}deg`,
          } as React.CSSProperties}
        />
      ))}
      {buds.map((b) => (
        <DroopingBud key={`bud-${b.id}`} x={b.x} y={b.y} delay={b.delay} />
      ))}
    </div>
  );
}
