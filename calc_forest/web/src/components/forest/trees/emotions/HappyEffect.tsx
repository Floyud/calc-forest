"use client";

import { useMemo } from "react";

interface ParticleProps {
  cx: number;
  cy: number;
  width: number;
  height: number;
  color: string;
}

function fourPointStarPath(size: number): string {
  const inner = size * 0.3;
  return `M0,${-size} C${inner * 0.4},${-inner * 0.4} ${inner * 0.4},${-inner * 0.4} ${inner},${-inner * 0.2} ` +
    `C${inner * 0.4},${inner * 0.1} ${inner * 0.4},${inner * 0.2} ${size * 0.1},${inner} ` +
    `C${inner * 0.1},${inner * 0.4} 0,${inner * 0.5} 0,${size} ` +
    `C${-inner * 0.1},${inner * 0.5} ${-inner * 0.1},${inner * 0.4} ${-size * 0.1},${inner} ` +
    `C${-inner * 0.4},${inner * 0.2} ${-inner * 0.4},${inner * 0.1} ${-inner},${-inner * 0.2} ` +
    `C${-inner * 0.4},${-inner * 0.4} ${-inner * 0.4},${-inner * 0.4} 0,${-size} Z`;
}

export function HappyEffect({ cx, cy, width, height, color }: ParticleProps) {
  void height;
  const sparkles = useMemo(() => {
    return Array.from({ length: 2 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.5,
      startY: cy - 5 + Math.random() * 15,
      delay: Math.random() * 4,
      duration: 2.5 + Math.random() * 2,
      size: 2.5 + Math.random() * 3,
    }));
  }, [cx, cy, width]);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {sparkles.map((s) => (
        <svg
          key={s.id}
          className="absolute"
          style={{
            left: s.x - s.size,
            top: s.startY - s.size,
            width: s.size * 2,
            height: s.size * 2,
            animation: `sparkle-twinkle ${s.duration}s ${s.delay}s infinite ease-in-out`,
            opacity: 0,
          }}
          viewBox={`${-s.size} ${-s.size} ${s.size * 2} ${s.size * 2}`}
        >
          <path d={fourPointStarPath(s.size)} fill={color} />
        </svg>
      ))}
      <svg
        className="absolute"
        style={{
          right: 0,
          top: cy - 14,
          width: 22,
          height: 18,
          animation: "bird-bob 2s infinite ease-in-out",
        }}
        viewBox="0 0 22 18"
      >
        <defs>
          <radialGradient id="bird-body" cx="40%" cy="35%">
            <stop offset="0%" stopColor="#FFB74D" />
            <stop offset="100%" stopColor="#FF9800" />
          </radialGradient>
        </defs>
        <ellipse cx="11" cy="12" rx="8" ry="5.5" fill="url(#bird-body)" />
        <circle cx="14" cy="8" r="5.5" fill="url(#bird-body)" />
        <circle cx="16" cy="7" r="1.8" fill="white" />
        <circle cx="16.3" cy="7" r="1" fill="#2C1810" />
        <circle cx="16.7" cy="6.5" r="0.35" fill="white" />
        <path d="M18.5,8 L21,8.5 L18.5,9.5" fill="#FF6F00" />
        <path d="M7,12 C5,11 3,12 4,14 C5,15 7,14 7,14" fill="#FFB74D" />
        <ellipse cx="10" cy="13" rx="2" ry="1.5" fill="rgba(255,255,255,0.2)" />
        <path d="M3,10 Q1,8 2,6" stroke="#FFB74D" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        <circle cx="2" cy="5.5" r="0.8" fill="#FF9800" />
      </svg>
    </div>
  );
}
