"use client";

import { memo, useMemo } from "react";
import type { EmotionState } from "@/lib/types";
import type { TreeColorConfig, CanopyType } from "./treeColors";
import { STAGE_SIZES } from "./treeColors";
import { ThrivingEffect } from "./emotions/ThrivingEffect";
import { HappyEffect } from "./emotions/HappyEffect";
import { WiltingEffect } from "./emotions/WiltingEffect";
import { StrugglingEffect } from "./emotions/StrugglingEffect";

interface SvgTreeProps {
  stage: string;
  emotion: EmotionState;
  colors: TreeColorConfig;
  speciesId?: string;
  size?: number;
  animate?: boolean;
}

function smoothCloudPath(cx: number, cy: number, r: number): string {
  const bumps = [
    { dx: -r * 0.45, dy: r * 0.05, sr: r * 0.58 },
    { dx: 0, dy: -r * 0.22, sr: r * 0.72 },
    { dx: r * 0.45, dy: r * 0.05, sr: r * 0.58 },
    { dx: -r * 0.15, dy: r * 0.25, sr: r * 0.48 },
    { dx: r * 0.2, dy: r * 0.2, sr: r * 0.48 },
  ];

  return bumps.map((b) => {
    const bx = cx + b.dx;
    const by = cy + b.dy;
    const br = b.sr;
    return `M${(bx - br).toFixed(1)},${by.toFixed(1)} ` +
      `C${(bx - br).toFixed(1)},${(by - br).toFixed(1)} ${(bx + br).toFixed(1)},${(by - br).toFixed(1)} ${(bx + br).toFixed(1)},${by.toFixed(1)} ` +
      `C${(bx + br).toFixed(1)},${(by + br).toFixed(1)} ${(bx - br).toFixed(1)},${(by + br).toFixed(1)} ${(bx - br).toFixed(1)},${by.toFixed(1)} Z`;
  }).join(" ");
}

function smoothStarPath(cx: number, cy: number, r: number): string {
  const lobes = 5;
  const innerR = r * 0.45;
  const pts: string[] = [];
  for (let i = 0; i < lobes * 2; i++) {
    const angle = (i / (lobes * 2)) * Math.PI * 2 - Math.PI / 2;
    const rad = i % 2 === 0 ? r : innerR;
    const px = cx + Math.cos(angle) * rad;
    const py = cy + Math.sin(angle) * rad;
    if (i === 0) {
      pts.push(`M${px.toFixed(1)},${py.toFixed(1)}`);
    } else {
      const prevAngle = ((i - 1) / (lobes * 2)) * Math.PI * 2 - Math.PI / 2;
      const prevRad = (i - 1) % 2 === 0 ? r : innerR;
      const midAngle = (prevAngle + angle) / 2;
      const cpRad = (prevRad + rad) / 2 * 1.1;
      const cpx = cx + Math.cos(midAngle) * cpRad;
      const cpy = cy + Math.sin(midAngle) * cpRad;
      pts.push(`Q${cpx.toFixed(1)},${cpy.toFixed(1)} ${px.toFixed(1)},${py.toFixed(1)}`);
    }
  }
  return pts.join(" ") + " Z";
}

function smoothPineTierPath(cx: number, cy: number, r: number): string {
  const tiers = 3;
  let d = "";
  for (let t = 0; t < tiers; t++) {
    const ty = cy - r * 0.5 + (t * r * 0.55);
    const halfW = r * (0.3 + t * 0.22);
    const topY = ty - r * 0.35;
    const botY = ty + r * 0.1;
    const leftX = cx - halfW;
    const rightX = cx + halfW;
    d += `M${cx.toFixed(1)},${topY.toFixed(1)} ` +
      `Q${cx.toFixed(1)},${(topY + 2).toFixed(1)} ${(leftX + halfW * 0.3).toFixed(1)},${((topY + botY) / 2).toFixed(1)} ` +
      `Q${leftX.toFixed(1)},${(botY - 2).toFixed(1)} ${leftX.toFixed(1)},${botY.toFixed(1)} ` +
      `L${rightX.toFixed(1)},${botY.toFixed(1)} ` +
      `Q${rightX.toFixed(1)},${(botY - 2).toFixed(1)} ${(rightX - halfW * 0.3).toFixed(1)},${((topY + botY) / 2).toFixed(1)} ` +
      `Q${cx.toFixed(1)},${(topY + 2).toFixed(1)} ${cx.toFixed(1)},${topY.toFixed(1)} Z `;
  }
  return d;
}

function smoothSpreadingPath(cx: number, cy: number, r: number): string {
  const w = r * 1.3;
  const h = r * 0.75;
  const startAngle = Math.PI;
  const endAngle = Math.PI * 2;
  const steps = 12;
  const pts: string[] = [];

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const angle = startAngle + t * (endAngle - startAngle);
    const px = cx + Math.cos(angle) * w;
    const py = cy + Math.sin(angle) * h;
    if (i === 0) {
      pts.push(`M${px.toFixed(1)},${py.toFixed(1)}`);
    } else {
      const prevAngle = startAngle + ((i - 1) / steps) * (endAngle - startAngle);
      const midAngle = (prevAngle + angle) / 2;
      const cpx = cx + Math.cos(midAngle) * w * 1.02;
      const cpy = cy + Math.sin(midAngle) * h * 0.98;
      pts.push(`Q${cpx.toFixed(1)},${cpy.toFixed(1)} ${px.toFixed(1)},${py.toFixed(1)}`);
    }
  }
  return pts.join(" ") + " Z";
}

function smoothOvalPath(cx: number, cy: number, r: number): string {
  const rx = r * 0.75;
  const ry = r * 0.9;
  return `M${(cx - rx).toFixed(1)},${cy.toFixed(1)} ` +
    `C${(cx - rx).toFixed(1)},${(cy - ry).toFixed(1)} ${(cx + rx).toFixed(1)},${(cy - ry).toFixed(1)} ${(cx + rx).toFixed(1)},${cy.toFixed(1)} ` +
    `C${(cx + rx).toFixed(1)},${(cy + ry).toFixed(1)} ${(cx - rx).toFixed(1)},${(cy + ry).toFixed(1)} ${(cx - rx).toFixed(1)},${cy.toFixed(1)} Z`;
}

function getCanopyPath(type: CanopyType, cx: number, cy: number, r: number): string {
  switch (type) {
    case "cloud": return smoothCloudPath(cx, cy, r);
    case "round": return smoothCloudPath(cx, cy, r * 0.95);
    case "oval": return smoothOvalPath(cx, cy, r);
    case "star": return smoothStarPath(cx, cy, r);
    case "triangle": return smoothPineTierPath(cx, cy, r);
    case "spreading": return smoothSpreadingPath(cx, cy, r);
    default: return smoothCloudPath(cx, cy, r);
  }
}

function InlineDefs({ colors }: { colors: TreeColorConfig }) {
  return (
    <defs>
      <linearGradient id="trunk-gradient" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor={colors.trunkLight} />
        <stop offset="40%" stopColor={colors.trunk} />
        <stop offset="100%" stopColor={colors.trunkDark} />
      </linearGradient>
      <linearGradient id="ground-gradient" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={colors.ground} />
        <stop offset="100%" stopColor={colors.groundDark} />
      </linearGradient>
      <radialGradient id="canopy-gradient" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stopColor={colors.leafLight} />
        <stop offset="60%" stopColor={colors.leaf} />
        <stop offset="100%" stopColor={colors.leafDark} />
      </radialGradient>
      <radialGradient id="fruit-gradient" cx="35%" cy="30%" r="60%">
        <stop offset="0%" stopColor={colors.fruit} stopOpacity={0.9} />
        <stop offset="100%" stopColor={colors.fruit} />
      </radialGradient>
      <radialGradient id="seed-mound" cx="50%" cy="30%" r="70%">
        <stop offset="0%" stopColor={colors.ground} />
        <stop offset="100%" stopColor={colors.groundDark} />
      </radialGradient>
    </defs>
  );
}

function Leaf({ x, y, r, color, delay = 0 }: {
  x: number; y: number; r: number; color: string; outline: string; delay?: number;
}) {
  const d = `M${x},${y - r} C${x + r * 0.6},${y - r * 0.6} ${x + r * 0.5},${y + r * 0.2} ${x},${y + r * 0.5} C${x - r * 0.5},${y + r * 0.2} ${x - r * 0.6},${y - r * 0.6} ${x},${y - r}`;
  return (
    <path
      d={d}
      fill={color}
      stroke="none"
      style={{
        transformOrigin: `${x}px ${y}px`,
        animation: `grow-in 0.35s ${delay}s ease-out both`,
        willChange: "transform",
      }}
    />
  );
}

function Canopy({ cx, cy, r, colors, stage, canopyType }: {
  cx: number; cy: number; r: number; colors: TreeColorConfig;
  stage: string; canopyType: CanopyType;
}) {
  const leafPositions = useMemo(() => {
    const positions: Array<{ x: number; y: number; r: number }> = [];
    const count = stage === "sprout" ? 2 : stage === "first_leaf" ? 4 : Math.floor(r / 3.5);

    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 + (i % 2) * 0.3;
      const dist = r * (0.25 + (i % 3) * 0.2);
      positions.push({
        x: cx + Math.cos(angle) * dist,
        y: cy + Math.sin(angle) * dist * 0.8,
        r: Math.max(4, r / (3.2 + (i % 2))),
      });
    }
    return positions;
  }, [cx, cy, r, stage]);

  if (stage === "sprout") {
    return (
      <g>
        <ellipse
          cx={cx - 5} cy={cy} rx={7} ry={4}
          fill={colors.leaf}
          style={{
            transformOrigin: `${cx - 5}px ${cy}px`,
            animation: "grow-in 0.35s 0.3s ease-out both",
            willChange: "transform",
          }}
        />
        <ellipse
          cx={cx + 5} cy={cy} rx={7} ry={4}
          fill={colors.leafLight}
          style={{
            transformOrigin: `${cx + 5}px ${cy}px`,
            animation: "grow-in 0.35s 0.4s ease-out both",
            willChange: "transform",
          }}
        />
        <ellipse
          cx={cx - 5} cy={cy - 0.5} rx={4} ry={2}
          fill="rgba(255,255,255,0.2)"
          style={{
            transformOrigin: `${cx - 5}px ${cy}px`,
            animation: "grow-in 0.35s 0.5s ease-out both",
          }}
        />
        <ellipse
          cx={cx + 5} cy={cy - 0.5} rx={4} ry={2}
          fill="rgba(255,255,255,0.2)"
          style={{
            transformOrigin: `${cx + 5}px ${cy}px`,
            animation: "grow-in 0.35s 0.6s ease-out both",
          }}
        />
      </g>
    );
  }

  const canopyPath = getCanopyPath(canopyType, cx, cy, r);

  return (
    <g>
      <path
        d={canopyPath}
        fill="url(#canopy-gradient)"
        fillRule="evenodd"
        filter="url(#tree-shadow)"
        style={{
          transformOrigin: `${cx}px ${cy}px`,
          animation: "grow-in 0.4s 0.15s ease-out both",
          willChange: "transform",
        }}
      />
      <path
        d={canopyPath}
        fill="url(#canopy-highlight)"
        fillRule="evenodd"
        style={{
          transformOrigin: `${cx}px ${cy}px`,
          animation: "grow-in 0.4s 0.2s ease-out both",
        }}
      />
      {leafPositions.map((lp, i) => (
        <Leaf
          key={i}
          x={lp.x} y={lp.y} r={lp.r}
          color={i % 3 === 0 ? colors.leafLight : colors.leaf}
          outline={colors.outline}
          delay={0.25 + i * 0.04}
        />
      ))}
      {(stage === "flowering" || stage === "bud" || stage === "mature") && (
        <Flowers cx={cx} cy={cy} r={r} colors={colors} stage={stage} />
      )}
    </g>
  );
}

function Flowers({ cx, cy, r, colors, stage }: {
  cx: number; cy: number; r: number; colors: TreeColorConfig; stage: string;
}) {
  const flowerCount = stage === "bud" ? 3 : stage === "flowering" ? 6 : 4;
  const flowers = [];
  for (let i = 0; i < flowerCount; i++) {
    const angle = (i / flowerCount) * Math.PI * 2 + 0.5;
    const dist = r * 0.55;
    flowers.push({
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist * 0.65,
      size: stage === "bud" ? 3 : 5,
    });
  }

  return (
    <g>
      {flowers.map((f, i) => (
        <g key={i} style={{
          transformOrigin: `${f.x}px ${f.y}px`,
          animation: `grow-in 0.35s ${0.7 + i * 0.08}s ease-out both`,
        }}>
          {stage === "bud" ? (
            <g>
              <ellipse cx={f.x} cy={f.y} rx={f.size} ry={f.size * 1.3}
                fill={colors.flower} filter="url(#tree-soft-shadow)"
              />
              <ellipse cx={f.x - 1} cy={f.y - 1} rx={f.size * 0.4} ry={f.size * 0.5}
                fill="rgba(255,255,255,0.3)"
              />
            </g>
          ) : (
            <g>
              {[0, 72, 144, 216, 288].map((deg) => {
                const petalDist = 3.5;
                const px = f.x + Math.cos((deg * Math.PI) / 180) * petalDist;
                const py = f.y + Math.sin((deg * Math.PI) / 180) * petalDist;
                return (
                  <g key={deg}>
                    <ellipse cx={px} cy={py} rx={3} ry={4}
                      fill={colors.flower}
                      transform={`rotate(${deg}, ${px}, ${py})`}
                    />
                    <circle cx={px + Math.cos((deg * Math.PI) / 180) * 0.8} cy={py + Math.sin((deg * Math.PI) / 180) * 0.8 - 0.5}
                      r={0.8} fill="rgba(255,255,255,0.5)"
                    />
                  </g>
                );
              })}
              <circle cx={f.x} cy={f.y} r={2.5}
                fill={colors.fruit}
              />
              <circle cx={f.x - 0.5} cy={f.y - 0.5} r={0.8}
                fill="rgba(255,255,255,0.4)"
              />
            </g>
          )}
        </g>
      ))}
      {stage === "mature" && (
        <>
          {flowers.slice(0, 3).map((f, i) => (
            <g
              key={`fruit-${i}`}
              style={{
                transformOrigin: `${f.x}px ${f.y + 7}px`,
                animation: `grow-in 0.4s ${1.1 + i * 0.12}s ease-out both`,
                willChange: "transform",
              }}
            >
              <circle
                cx={f.x + (i % 2 ? 5 : -5)}
                cy={f.y + 7}
                r={5.5}
                fill="url(#fruit-gradient)"
                filter="url(#tree-soft-shadow)"
              />
              <circle
                cx={f.x + (i % 2 ? 5 : -5) - 1.5}
                cy={f.y + 5.5}
                r={1.5}
                fill="rgba(255,255,255,0.35)"
              />
            </g>
          ))}
        </>
      )}
    </g>
  );
}

function Trunk({ cx, baseY, height, width, colors, stage }: {
  cx: number; baseY: number; height: number; width: number; colors: TreeColorConfig; stage: string;
}) {
  if (height <= 0) return null;

  const topW = width * 0.25;
  const hasBranches = ["branching", "sturdy", "bud", "flowering", "mature"].includes(stage);

  const trunkPath = [
    `M${cx - width / 2},${baseY}`,
    `C${cx - width / 2},${baseY - height * 0.4} ${cx - topW / 2 - 1},${baseY - height * 0.6} ${cx - topW / 2},${baseY - height}`,
    `L${cx + topW / 2},${baseY - height}`,
    `C${cx + topW / 2 + 1},${baseY - height * 0.6} ${cx + width / 2},${baseY - height * 0.4} ${cx + width / 2},${baseY}`,
    "Z",
  ].join(" ");

  const trunkGrowStyle = {
    transformOrigin: `${cx}px ${baseY}px`,
    animation: "grow-y 0.6s ease-out both",
    willChange: "transform" as const,
  };

  const barkGrowStyle = {
    transformOrigin: `${cx}px ${baseY}px`,
    animation: "grow-y 0.6s ease-out both",
  };

  return (
    <g>
      <path
        d={trunkPath}
        fill="url(#trunk-gradient)"
        filter="url(#tree-soft-shadow)"
        style={trunkGrowStyle}
      />
      <path
        d={`M${cx - 1},${baseY - 3} C${cx - 0.5},${baseY - height * 0.3} ${cx + 0.5},${baseY - height * 0.6} ${cx + 0.3},${baseY - height + 4}`}
        stroke={colors.trunkDark}
        strokeWidth={0.6}
        fill="none"
        strokeLinecap="round"
        opacity={0.2}
        style={barkGrowStyle}
      />
      <path
        d={`M${cx + 1.5},${baseY - 5} C${cx + 1},${baseY - height * 0.4} ${cx + 0.8},${baseY - height * 0.7} ${cx + 0.6},${baseY - height + 6}`}
        stroke={colors.trunkDark}
        strokeWidth={0.4}
        fill="none"
        strokeLinecap="round"
        opacity={0.15}
        style={barkGrowStyle}
      />
      {hasBranches && (
        <>
          <path
            d={`M${cx - 2},${baseY - height * 0.5} C${cx - width * 0.8},${baseY - height * 0.52} ${cx - width * 1.2},${baseY - height * 0.58} ${cx - width * 1.3},${baseY - height * 0.62}`}
            stroke="url(#trunk-gradient)"
            strokeWidth={stage === "mature" ? 2.5 : 2}
            fill="none"
            strokeLinecap="round"
            style={{
              strokeDasharray: 80,
              animation: "draw-in 0.4s 0.4s ease-out both",
              willChange: "stroke-dashoffset",
            }}
          />
          <path
            d={`M${cx + 2},${baseY - height * 0.45} C${cx + width * 0.7},${baseY - height * 0.48} ${cx + width * 1.0},${baseY - height * 0.54} ${cx + width * 1.2},${baseY - height * 0.58}`}
            stroke="url(#trunk-gradient)"
            strokeWidth={stage === "mature" ? 2.5 : 2}
            fill="none"
            strokeLinecap="round"
            style={{
              strokeDasharray: 80,
              animation: "draw-in 0.4s 0.5s ease-out both",
              willChange: "stroke-dashoffset",
            }}
          />
        </>
      )}
    </g>
  );
}

function Ground({ cx, baseY, colors }: { cx: number; baseY: number; colors: TreeColorConfig }) {
  const hillPath = `M${cx - 30},${baseY + 3} C${cx - 20},${baseY - 2} ${cx - 8},${baseY - 1} ${cx},${baseY + 1} C${cx + 8},${baseY - 1} ${cx + 20},${baseY - 2} ${cx + 30},${baseY + 3}`;

  return (
    <g>
      <path
        d={hillPath}
        fill="url(#ground-gradient)"
        opacity={0.6}
        style={{
          transformOrigin: `${cx}px ${baseY}px`,
          animation: "grow-x 0.3s 0.1s ease-out both",
        }}
      />
      <ellipse cx={cx} cy={baseY + 5} rx={26} ry={5}
        fill={colors.groundDark} opacity={0.15}
      />
      {[{ x: -12 }, { x: -4 }, { x: 5 }, { x: 13 }].map(({ x: gx }, i) => (
        <path
          key={i}
          d={`M${cx + gx},${baseY} Q${cx + gx + 0.5},${baseY - 3} ${cx + gx + 1},${baseY - 5}`}
          stroke={colors.leafLight}
          strokeWidth={1}
          strokeLinecap="round"
          fill="none"
          opacity={0.5}
          style={{
            strokeDasharray: 20,
            animation: `draw-in 0.2s ${0.5 + i * 0.06}s ease-out both`,
          }}
        />
      ))}
    </g>
  );
}

function SeedStage({ cx, baseY, colors }: { cx: number; baseY: number; colors: TreeColorConfig }) {
  const moundPath = `M${cx - 16},${baseY + 1} C${cx - 12},${baseY - 5} ${cx - 5},${baseY - 6} ${cx},${baseY - 5} C${cx + 5},${baseY - 6} ${cx + 12},${baseY - 5} ${cx + 16},${baseY + 1}`;

  return (
    <g>
      <path d={moundPath}
        fill="url(#seed-mound)"
      />
      <ellipse cx={cx} cy={baseY - 2} rx={10} ry={2}
        fill={colors.groundDark} opacity={0.15}
      />
      <path
        d={`M${cx},${baseY - 5} C${cx + 1},${baseY - 10} ${cx + 1.5},${baseY - 12} ${cx + 1.5},${baseY - 16}`}
        stroke={colors.leaf}
        strokeWidth={2.5}
        fill="none"
        strokeLinecap="round"
        style={{
          strokeDasharray: 30,
          animation: "draw-in 0.5s 0.3s ease-out both",
        }}
      />
      <path
        d={`M${cx + 1.5},${baseY - 16} C${cx + 5},${baseY - 18} ${cx + 6},${baseY - 20} ${cx + 4},${baseY - 20}`}
        fill={colors.leaf}
        style={{
          transformOrigin: `${cx + 1.5}px ${baseY - 16}px`,
          animation: "grow-in 0.35s 0.7s ease-out both",
        }}
      />
      <path
        d={`M${cx + 1.5},${baseY - 16} C${cx - 3},${baseY - 18} ${cx - 4},${baseY - 20} ${cx - 2},${baseY - 20}`}
        fill={colors.leafLight}
        style={{
          transformOrigin: `${cx + 1.5}px ${baseY - 16}px`,
          animation: "grow-in 0.35s 0.85s ease-out both",
        }}
      />
      <ellipse
        cx={cx + 2} cy={baseY - 17.5} rx={2} ry={1.2}
        fill="rgba(255,255,255,0.3)"
        style={{
          transformOrigin: `${cx + 2}px ${baseY - 17.5}px`,
          animation: "grow-in 0.35s 1s ease-out both",
        }}
      />
    </g>
  );
}

const SWAY_CLASS_MAP: Record<EmotionState, string> = {
  thriving: "tree-sway-thriving",
  happy: "tree-sway",
  stable: "tree-sway",
  wilting: "tree-sway",
  struggling: "tree-sway-struggling",
};

export const SvgTree = memo(function SvgTree({
  stage,
  emotion,
  colors,
  size,
  animate = true,
}: SvgTreeProps) {
  const config = STAGE_SIZES[stage] || STAGE_SIZES.seed;
  const w = size || config.width;
  const h = size ? size * (config.height / config.width) : config.height;
  const cx = w / 2;
  const baseY = h - 10;
  const trunkH = config.trunkH * (w / config.width);
  const crownR = config.crownR * (w / config.width);
  const trunkW = Math.max(3, 6 * (w / config.width));
  const crownCy = baseY - trunkH - crownR * 0.4;

  const canopyType = colors.canopyType || "cloud";
  const swayClass = animate ? SWAY_CLASS_MAP[emotion] : "";

  return (
    <div className="relative" style={{ width: w, height: h }}>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        width={w}
        height={h}
        style={{
          overflow: "visible",
          willChange: "transform",
          animation: swayClass ? `${swayClass} ${emotion === "struggling" ? 2 : emotion === "thriving" ? 3 : 4}s infinite ease-in-out` : undefined,
        }}
      >
        <InlineDefs colors={colors} />
        {emotion === "thriving" && (
          <circle cx={cx} cy={crownCy} r={crownR * 1.8} fill="url(#thriving-glow)" />
        )}
        {stage === "seed" ? (
          <SeedStage cx={cx} baseY={baseY} colors={colors} />
        ) : (
          <>
            <Ground cx={cx} baseY={baseY} colors={colors} />
            <Trunk cx={cx} baseY={baseY} height={trunkH} width={trunkW} colors={colors} stage={stage} />
            <Canopy cx={cx} cy={crownCy} r={crownR} colors={colors} stage={stage} canopyType={canopyType} />
          </>
        )}
      </svg>

      {animate && emotion === "thriving" && (
        <ThrivingEffect cx={cx} cy={crownCy} width={w} height={h} color={colors.particle} />
      )}
      {animate && emotion === "happy" && (
        <HappyEffect cx={cx} cy={crownCy} width={w} height={h} color={colors.particle} />
      )}
      {animate && emotion === "wilting" && (
        <WiltingEffect cx={cx} cy={crownCy} width={w} height={h} color={colors.particle} />
      )}
      {animate && emotion === "struggling" && (
        <StrugglingEffect cx={cx} cy={crownCy} width={w} height={h} color={colors.particle} />
      )}
    </div>
  );
});
