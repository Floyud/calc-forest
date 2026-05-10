"use client";

import { useMemo } from "react";

interface ParticleProps {
  cx: number;
  cy: number;
  width: number;
  height: number;
  color: string;
}

export function StrugglingEffect({ cx, cy, width, height, color }: ParticleProps) {
  void height;
  const rainDrops = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.9,
      startY: -8,
      delay: Math.random() * 2,
      duration: 0.5 + Math.random() * 0.4,
    }));
  }, [cx, width]);

  const mistWisps = useMemo(() => {
    return Array.from({ length: 3 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.5,
      y: cy + 5 + Math.random() * 15,
      delay: i * 1.5,
      duration: 4 + Math.random() * 2,
    }));
  }, [cx, cy, width]);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {rainDrops.map((r) => (
        <svg
          key={`rain-${r.id}`}
          className="absolute"
          style={{
            left: r.x - 3,
            top: r.startY,
            width: 6,
            height: 10,
            animation: `rain-fall ${r.duration}s ${r.delay}s infinite linear`,
          }}
          viewBox="0 0 6 10"
        >
          <path
            d="M3,0 C5,3 5,5 5,6.5 C5,8.5 4,10 3,10 C2,10 1,8.5 1,6.5 C1,5 1,3 3,0 Z"
            fill={color}
            opacity={0.4}
          />
          <ellipse cx="2.2" cy="5" rx="0.6" ry="1.5" fill="rgba(255,255,255,0.25)" />
        </svg>
      ))}
      {mistWisps.map((m) => (
        <svg
          key={`mist-${m.id}`}
          className="absolute"
          style={{
            left: m.x - 20,
            top: m.y,
            width: 40,
            height: 12,
            animation: `mist-float ${m.duration}s ${m.delay}s infinite ease-in-out`,
            opacity: 0,
          }}
          viewBox="0 0 40 12"
        >
          <path
            d="M0,8 C5,4 10,6 15,7 C20,8 25,5 30,6 C35,7 38,5 40,7"
            stroke="rgba(255,255,255,0.35)"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />
          <path
            d="M2,10 C8,7 14,9 20,8 C26,7 32,9 38,8"
            stroke="rgba(255,255,255,0.2)"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
          />
        </svg>
      ))}
    </div>
  );
}
