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
  const s = size;
  const inner = s * 0.3;
  return `M0,${-s} C${inner * 0.4},${-inner * 0.4} ${inner * 0.4},${-inner * 0.4} ${inner},${-inner * 0.2} ` +
    `C${inner * 0.4},${inner * 0.1} ${inner * 0.4},${inner * 0.2} ${s * 0.1},${inner} ` +
    `C${inner * 0.1},${inner * 0.4} 0,${inner * 0.5} 0,${s} ` +
    `C${-inner * 0.1},${inner * 0.5} ${-inner * 0.1},${inner * 0.4} ${-s * 0.1},${inner} ` +
    `C${-inner * 0.4},${inner * 0.2} ${-inner * 0.4},${inner * 0.1} ${-inner},${-inner * 0.2} ` +
    `C${-inner * 0.4},${-inner * 0.4} ${-inner * 0.4},${-inner * 0.4} 0,${-s} Z`;
}

export function ThrivingEffect({ cx, cy, width, height, color }: ParticleProps) {
  void height;
  const sparkles = useMemo(() => {
    return Array.from({ length: 3 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.8,
      startY: cy + Math.random() * 20,
      delay: Math.random() * 3,
      duration: 2 + Math.random() * 2,
      size: 3 + Math.random() * 4,
    }));
  }, [cx, cy, width]);

  const butterflies = useMemo(() => {
    const wingColors = [
      { main: "#FF6B9D", accent: "#FF9EC5" },
      { main: "#B388FF", accent: "#D1B3FF" },
      { main: "#4DD0E1", accent: "#80DEEA" },
    ];
    return Array.from({ length: 1 }, (_, i) => ({
      id: i,
      wingMain: wingColors[i % wingColors.length].main,
      wingAccent: wingColors[i % wingColors.length].accent,
      radiusX: 18 + Math.random() * 10,
      radiusY: 10 + Math.random() * 5,
      phase: Math.random() * Math.PI * 2,
      speed: 4 + Math.random() * 2,
    }));
  }, []);

  const hearts = useMemo(() => {
    return Array.from({ length: 1 }, (_, i) => ({
      id: i,
      x: cx + (Math.random() - 0.5) * width * 0.5,
      startY: cy + Math.random() * 10,
      delay: 1 + Math.random() * 4,
      duration: 3 + Math.random() * 2,
      size: 2 + Math.random() * 2,
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
            animation: `sparkle-rise ${s.duration}s ${s.delay}s infinite ease-out`,
            opacity: 0,
          }}
          viewBox={`${-s.size} ${-s.size} ${s.size * 2} ${s.size * 2}`}
        >
          <path d={fourPointStarPath(s.size)} fill={color} />
        </svg>
      ))}
      {butterflies.map((b) => (
        <svg
          key={`bf-${b.id}`}
          className="absolute"
          style={{
            left: cx - 14,
            top: cy - 22,
            width: 28,
            height: 22,
            animation: `butterfly-orbit ${b.speed}s ${b.id * 1.5}s infinite linear`,
          }}
          viewBox="0 0 28 22"
        >
          <defs>
            <radialGradient id={`bf-wing-${b.id}-l`} cx="30%" cy="30%">
              <stop offset="0%" stopColor={b.wingAccent} />
              <stop offset="100%" stopColor={b.wingMain} />
            </radialGradient>
            <radialGradient id={`bf-wing-${b.id}-r`} cx="30%" cy="30%">
              <stop offset="0%" stopColor={b.wingAccent} />
              <stop offset="100%" stopColor={b.wingMain} />
            </radialGradient>
          </defs>
          <ellipse cx="7" cy="11" rx="6" ry="8" fill={`url(#bf-wing-${b.id}-l)`}>
            <animateTransform attributeName="transform" type="scale" values="1 1;1 0.4;1 1" dur="0.3s" repeatCount="indefinite" />
          </ellipse>
          <circle cx="5" cy="6" r="1.5" fill="rgba(255,255,255,0.5)" />
          <ellipse cx="21" cy="11" rx="6" ry="8" fill={`url(#bf-wing-${b.id}-r)`}>
            <animateTransform attributeName="transform" type="scale" values="1 1;1 0.4;1 1" dur="0.3s" repeatCount="indefinite" />
          </ellipse>
          <circle cx="23" cy="6" r="1.5" fill="rgba(255,255,255,0.5)" />
          <ellipse cx="14" cy="11" rx="1.8" ry="5" fill="#4A3728" />
          <line x1="11" y1="6" x2="8" y2="2" stroke="#4A3728" strokeWidth="0.6" strokeLinecap="round" />
          <line x1="17" y1="6" x2="20" y2="2" stroke="#4A3728" strokeWidth="0.6" strokeLinecap="round" />
          <circle cx="8" cy="2" r="0.8" fill={b.wingMain} />
          <circle cx="20" cy="2" r="0.8" fill={b.wingMain} />
        </svg>
      ))}
      {hearts.map((h) => (
        <svg
          key={`heart-${h.id}`}
          className="absolute"
          style={{
            left: h.x - h.size,
            top: h.startY,
            width: h.size * 2,
            height: h.size * 2,
            animation: `sparkle-rise ${h.duration}s ${h.delay}s infinite ease-out`,
            opacity: 0,
          }}
          viewBox="0 0 10 10"
        >
          <path
            d="M5,8 C5,8 1,5.5 1,3 C1,1.5 2.5,0.5 3.5,1.5 C4,2 4.5,2.5 5,3.5 C5.5,2.5 6,2 6.5,1.5 C7.5,0.5 9,1.5 9,3 C9,5.5 5,8 5,8 Z"
            fill="#FF6B9D"
            opacity={0.7}
          />
        </svg>
      ))}
    </div>
  );
}
