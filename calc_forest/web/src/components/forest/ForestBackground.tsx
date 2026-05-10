"use client";

import { useMemo } from "react";
import type { EmotionState } from "@/lib/types";

const SKY_GRADIENTS: Record<EmotionState, { from: string; to: string }> = {
  thriving: { from: "#fef3c7", to: "#fde68a" },
  happy: { from: "#dbeafe", to: "#bfdbfe" },
  stable: { from: "#e0f2fe", to: "#bae6fd" },
  wilting: { from: "#f1f5f9", to: "#cbd5e1" },
  struggling: { from: "#e2e8f0", to: "#94a3b8" },
};

interface ForestBackgroundProps {
  emotion: EmotionState;
  children: React.ReactNode;
}

export function ForestBackground({ emotion, children }: ForestBackgroundProps) {
  const sky = SKY_GRADIENTS[emotion] || SKY_GRADIENTS.stable;

  const sparklePositions = useMemo(() =>
    Array.from({ length: 6 }, (_, i) => ({
      left: `${5 + (i * 8) % 90}%`,
      top: `${10 + (i * 17) % 40}%`,
      width: 2 + (i % 3),
      height: 2 + (i % 3),
      delay: i * 0.4,
      duration: 2 + i % 3,
    })),
    [],
  );

  const rainPositions = useMemo(() =>
    Array.from({ length: 8 }, (_, i) => ({
      left: `${i * 5}%`,
      height: 10 + (i % 4) * 3,
      delay: (i % 5) * 0.2,
      duration: 0.5 + (i % 3) * 0.15,
    })),
    [],
  );

  return (
    <div className="relative min-h-[600px] overflow-hidden rounded-2xl">
      <div
        className="absolute inset-0 transition-colors duration-1000"
        style={{
          background: `linear-gradient(180deg, ${sky.from} 0%, ${sky.to} 50%, #f0fdf4 70%, #dcfce7 85%, #bbf7d0 100%)`,
        }}
      />

      <div className="absolute bottom-0 left-0 right-0 h-24 overflow-hidden opacity-30">
        <svg viewBox="0 0 1200 60" className="w-full" preserveAspectRatio="none">
          <path d="M0,30 Q100,10 200,25 Q300,40 400,20 Q500,5 600,30 Q700,50 800,25 Q900,10 1000,35 Q1100,50 1200,30 L1200,60 L0,60 Z" fill="#86efac" />
          <path d="M0,40 Q150,25 300,35 Q450,50 600,30 Q750,15 900,40 Q1050,55 1200,35 L1200,60 L0,60 Z" fill="#4ade80" opacity="0.5" />
        </svg>
      </div>

      {emotion === "thriving" && (
        <div className="absolute inset-0 pointer-events-none">
          {sparklePositions.map((s, i) => (
            <div
              key={i}
              className="absolute rounded-full"
              style={{
                left: s.left,
                top: s.top,
                width: s.width,
                height: s.height,
                backgroundColor: "#fde68a",
                opacity: 0,
                animation: `sparkle-twinkle ${s.duration}s ${s.delay}s infinite ease-in-out`,
              }}
            />
          ))}
        </div>
      )}

      {emotion === "struggling" && (
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute inset-0"
            style={{
              background: "linear-gradient(180deg, rgba(148,163,184,0.15) 0%, transparent 60%)",
            }}
          />
          {rainPositions.map((r, i) => (
            <div
              key={i}
              className="absolute"
              style={{
                left: r.left,
                top: -10,
                width: 1,
                height: r.height,
                backgroundColor: "rgba(148,163,184,0.25)",
                animation: `rain-fall ${r.duration}s ${r.delay}s infinite linear`,
              }}
            />
          ))}
        </div>
      )}

      <div className="relative z-10">{children}</div>
    </div>
  );
}
