import type { EmotionState } from "@/lib/types";
import type { TreeColorConfig, CanopyType } from "../trees/treeColors";
import { STAGE_SIZES } from "../trees/treeColors";

export interface TreeRenderParams {
  stage: string;
  emotion: EmotionState;
  colors: TreeColorConfig;
  size?: number;
  time: number;
  mountTime: number;
}

/** Pre-computed color cache for a tree */
interface ColorCache {
  leaf: RGBColor;
  leafLight: RGBColor;
  leafDark: RGBColor;
}

function buildColorCache(colors: TreeColorConfig): ColorCache {
  return {
    leaf: hexToRgb(colors.leaf),
    leafLight: hexToRgb(colors.leafLight),
    leafDark: hexToRgb(colors.leafDark),
  };
}

// ─── Utility helpers ─────────────────────────────────────────────────────────

function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

function prog(elapsed: number, duration: number, delay = 0): number {
  if (elapsed < delay) return 0;
  return easeOut(Math.min(1, (elapsed - delay) / duration));
}

/** Deterministic micro-jitter for hand-drawn feel */
function jit(v: number, seed: number, amt = 0.35): number {
  return v + Math.sin(seed * 127.1 + v * 311.7) * amt;
}

/** Pre-computed RGB for breathe optimization */
interface RGBColor { r: number; g: number; b: number; }

function hexToRgb(hex: string): RGBColor {
  return {
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  };
}

function breatheRgb(color: RGBColor, time: number, amt = 0.025): string {
  const s = Math.sin(time * 0.0008) * amt * 255;
  const c = (n: number) => Math.max(0, Math.min(255, Math.round(n)));
  return `rgb(${c(color.r + s)},${c(color.g + s * 0.5)},${c(color.b - s * 0.3)})`;
}

/** Subtle brightness breathing for living feel */
function breathe(hex: string, time: number, amt = 0.025): string {
  return breatheRgb(hexToRgb(hex), time, amt);
}

function rgba(r: number, g: number, b: number, a: number): string {
  return `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${a})`;
}

// ─── Shadow helpers ──────────────────────────────────────────────────────────

type ShadowKind = "main" | "soft" | "glow" | "none";

function shadow(ctx: CanvasRenderingContext2D, kind: ShadowKind, glowCol?: string) {
  switch (kind) {
    case "main":
      ctx.shadowColor = "rgba(0,0,0,0.12)";
      ctx.shadowBlur = 3;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 2;
      break;
    case "soft":
      ctx.shadowColor = "rgba(0,0,0,0.08)";
      ctx.shadowBlur = 1.5;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 1;
      break;
    case "glow":
      ctx.shadowColor = glowCol ?? "rgba(255,213,79,0.5)";
      ctx.shadowBlur = 12;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;
      break;
    case "none":
      ctx.shadowColor = "transparent";
      ctx.shadowBlur = 0;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;
      break;
  }
}

// ─── Canopy path builders (Canvas2D) ─────────────────────────────────────────

function cloudPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number, sd = 0) {
  const bumps = [
    { dx: -r * 0.45, dy: r * 0.05, sr: r * 0.58 },
    { dx: 0, dy: -r * 0.22, sr: r * 0.72 },
    { dx: r * 0.45, dy: r * 0.05, sr: r * 0.58 },
    { dx: -r * 0.15, dy: r * 0.25, sr: r * 0.48 },
    { dx: r * 0.2, dy: r * 0.2, sr: r * 0.48 },
  ];
  for (let i = 0; i < bumps.length; i++) {
    const b = bumps[i];
    const bx = jit(cx + b.dx, sd + i * 13, 0.3);
    const by = jit(cy + b.dy, sd + i * 17, 0.3);
    const br = b.sr;
    ctx.moveTo(bx - br, by);
    ctx.bezierCurveTo(bx - br, by - br, bx + br, by - br, bx + br, by);
    ctx.bezierCurveTo(bx + br, by + br, bx - br, by + br, bx - br, by);
    ctx.closePath();
  }
}

function starPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
  const lobes = 5;
  const innerR = r * 0.45;
  for (let i = 0; i < lobes * 2; i++) {
    const angle = (i / (lobes * 2)) * Math.PI * 2 - Math.PI / 2;
    const rad = i % 2 === 0 ? r : innerR;
    const px = cx + Math.cos(angle) * rad;
    const py = cy + Math.sin(angle) * rad;
    if (i === 0) {
      ctx.moveTo(px, py);
    } else {
      const prevA = ((i - 1) / (lobes * 2)) * Math.PI * 2 - Math.PI / 2;
      const prevR = (i - 1) % 2 === 0 ? r : innerR;
      const midA = (prevA + angle) / 2;
      const cpR = ((prevR + rad) / 2) * 1.1;
      ctx.quadraticCurveTo(cx + Math.cos(midA) * cpR, cy + Math.sin(midA) * cpR, px, py);
    }
  }
  ctx.closePath();
}

function pineTierPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
  for (let t = 0; t < 3; t++) {
    const ty = cy - r * 0.5 + t * r * 0.55;
    const hw = r * (0.3 + t * 0.22);
    const topY = ty - r * 0.35;
    const botY = ty + r * 0.1;
    const lx = cx - hw;
    const rx = cx + hw;
    ctx.moveTo(cx, topY);
    ctx.quadraticCurveTo(cx, topY + 2, lx + hw * 0.3, (topY + botY) / 2);
    ctx.quadraticCurveTo(lx, botY - 2, lx, botY);
    ctx.lineTo(rx, botY);
    ctx.quadraticCurveTo(rx, botY - 2, rx - hw * 0.3, (topY + botY) / 2);
    ctx.quadraticCurveTo(cx, topY + 2, cx, topY);
    ctx.closePath();
  }
}

function spreadingPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
  const w = r * 1.3;
  const h = r * 0.75;
  const s0 = Math.PI;
  const s1 = Math.PI * 2;
  const steps = 12;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const a = s0 + t * (s1 - s0);
    const px = cx + Math.cos(a) * w;
    const py = cy + Math.sin(a) * h;
    if (i === 0) { ctx.moveTo(px, py); continue; }
    const prevA = s0 + ((i - 1) / steps) * (s1 - s0);
    const midA = (prevA + a) / 2;
    ctx.quadraticCurveTo(cx + Math.cos(midA) * w * 1.02, cy + Math.sin(midA) * h * 0.98, px, py);
  }
  ctx.closePath();
}

function ovalPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
  const rx = r * 0.75;
  const ry = r * 0.9;
  ctx.moveTo(cx - rx, cy);
  ctx.bezierCurveTo(cx - rx, cy - ry, cx + rx, cy - ry, cx + rx, cy);
  ctx.bezierCurveTo(cx + rx, cy + ry, cx - rx, cy + ry, cx - rx, cy);
  ctx.closePath();
}

function canopyPath(
  ctx: CanvasRenderingContext2D,
  type: CanopyType,
  cx: number,
  cy: number,
  r: number,
  sd = 0,
) {
  ctx.beginPath();
  switch (type) {
    case "cloud": cloudPath(ctx, cx, cy, r, sd); break;
    case "round": cloudPath(ctx, cx, cy, r * 0.95, sd); break;
    case "oval": ovalPath(ctx, cx, cy, r); break;
    case "star": starPath(ctx, cx, cy, r); break;
    case "triangle": pineTierPath(ctx, cx, cy, r); break;
    case "spreading": spreadingPath(ctx, cx, cy, r); break;
    default: cloudPath(ctx, cx, cy, r, sd); break;
  }
}

// ─── Sway ─────────────────────────────────────────────────────────────────────

function swayAngle(emotion: EmotionState, time: number): number {
  const t = time * 0.001;
  const d = Math.PI / 180;
  switch (emotion) {
    case "thriving": return Math.sin(t * (2 * Math.PI) / 3) * 1.5 * d;
    case "happy":
    case "stable": return Math.sin(t * (2 * Math.PI) / 4) * 0.8 * d;
    case "wilting": return Math.sin(t * (2 * Math.PI) / 4) * 0.5 * d;
    case "struggling": return (Math.sin(t * Math.PI) * 1.5 - 0.5) * d;
    default: return Math.sin(t * (2 * Math.PI) / 4) * 0.8 * d;
  }
}

// ─── Sub-component renderers ─────────────────────────────────────────────────

function drawGround(
  ctx: CanvasRenderingContext2D,
  cx: number,
  baseY: number,
  colors: TreeColorConfig,
  elapsed: number,
) {
  const gp = prog(elapsed, 300, 100);
  if (gp <= 0) return;

  ctx.save();
  ctx.translate(cx, baseY);
  ctx.scale(gp, 1);
  ctx.translate(-cx, -baseY);

  // hill
  const gGrad = ctx.createLinearGradient(cx, baseY - 2, cx, baseY + 5);
  gGrad.addColorStop(0, colors.ground);
  gGrad.addColorStop(1, colors.groundDark);
  ctx.fillStyle = gGrad;
  ctx.globalAlpha = 0.6;
  ctx.beginPath();
  ctx.moveTo(cx - 30, baseY + 3);
  ctx.bezierCurveTo(cx - 20, baseY - 2, cx - 8, baseY - 1, cx, baseY + 1);
  ctx.bezierCurveTo(cx + 8, baseY - 1, cx + 20, baseY - 2, cx + 30, baseY + 3);
  ctx.fill();
  ctx.globalAlpha = 1;

  // shadow ellipse
  ctx.beginPath();
  ctx.ellipse(cx, baseY + 5, 26, 5, 0, 0, Math.PI * 2);
  ctx.fillStyle = colors.groundDark;
  ctx.globalAlpha = 0.15;
  ctx.fill();
  ctx.globalAlpha = 1;

  // grass blades
  const gxs = [-12, -4, 5, 13];
  for (let i = 0; i < gxs.length; i++) {
    const gprog = prog(elapsed, 200, 500 + i * 60);
    if (gprog <= 0) continue;
    ctx.beginPath();
    ctx.moveTo(cx + gxs[i], baseY);
    ctx.quadraticCurveTo(cx + gxs[i] + 0.5, baseY - 3, cx + gxs[i] + 1, baseY - 5);
    ctx.strokeStyle = colors.leafLight;
    ctx.lineWidth = 1;
    ctx.lineCap = "round";
    ctx.globalAlpha = 0.5 * gprog;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  ctx.restore();
}

function drawTrunk(
  ctx: CanvasRenderingContext2D,
  cx: number,
  baseY: number,
  height: number,
  width: number,
  colors: TreeColorConfig,
  stage: string,
  elapsed: number,
  scale: number,
) {
  if (height <= 0) return;
  const tp = prog(elapsed, 600, 0);
  if (tp <= 0) return;

  const topW = width * 0.25;
  const hasBranch = ["branching", "sturdy", "bud", "flowering", "mature"].includes(stage);

  ctx.save();
  // trunk grow from base
  ctx.translate(cx, baseY);
  ctx.scale(1, tp);
  ctx.translate(-cx, -baseY);

  // trunk body
  const tGrad = ctx.createLinearGradient(cx - width / 2, 0, cx + width / 2, 0);
  tGrad.addColorStop(0, colors.trunkLight);
  tGrad.addColorStop(0.4, colors.trunk);
  tGrad.addColorStop(1, colors.trunkDark);

  shadow(ctx, "soft");
  ctx.beginPath();
  ctx.moveTo(cx - width / 2, baseY);
  ctx.bezierCurveTo(
    cx - width / 2, baseY - height * 0.4,
    cx - topW / 2 - 1, baseY - height * 0.6,
    cx - topW / 2, baseY - height,
  );
  ctx.lineTo(cx + topW / 2, baseY - height);
  ctx.bezierCurveTo(
    cx + topW / 2 + 1, baseY - height * 0.6,
    cx + width / 2, baseY - height * 0.4,
    cx + width / 2, baseY,
  );
  ctx.closePath();
  ctx.fillStyle = tGrad;
  ctx.fill();
  shadow(ctx, "none");

  // bark lines
  ctx.globalAlpha = 0.2;
  ctx.strokeStyle = colors.trunkDark;
  ctx.lineWidth = 0.6;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(cx - 1, baseY - 3);
  ctx.bezierCurveTo(cx - 0.5, baseY - height * 0.3, cx + 0.5, baseY - height * 0.6, cx + 0.3, baseY - height + 4);
  ctx.stroke();
  ctx.globalAlpha = 0.15;
  ctx.lineWidth = 0.4;
  ctx.beginPath();
  ctx.moveTo(cx + 1.5, baseY - 5);
  ctx.bezierCurveTo(cx + 1, baseY - height * 0.4, cx + 0.8, baseY - height * 0.7, cx + 0.6, baseY - height + 6);
  ctx.stroke();
  ctx.globalAlpha = 1;

  // branches
  if (hasBranch) {
    const sw = stage === "mature" ? 2.5 : 2;
    const bGrad = ctx.createLinearGradient(cx - width * 1.3, 0, cx + width * 1.2, 0);
    bGrad.addColorStop(0, colors.trunkLight);
    bGrad.addColorStop(0.4, colors.trunk);
    bGrad.addColorStop(1, colors.trunkDark);
    ctx.strokeStyle = bGrad;
    ctx.lineWidth = sw;
    ctx.lineCap = "round";

    // left branch
    const lp = prog(elapsed, 400, 400);
    if (lp > 0) {
      ctx.save();
      ctx.setLineDash([80]);
      ctx.lineDashOffset = 80 * (1 - lp);
      ctx.beginPath();
      ctx.moveTo(cx - 2, baseY - height * 0.5);
      ctx.bezierCurveTo(cx - width * 0.8, baseY - height * 0.52, cx - width * 1.2, baseY - height * 0.58, cx - width * 1.3, baseY - height * 0.62);
      ctx.stroke();
      ctx.restore();
    }

    // right branch
    const rp = prog(elapsed, 400, 500);
    if (rp > 0) {
      ctx.save();
      ctx.setLineDash([80]);
      ctx.lineDashOffset = 80 * (1 - rp);
      ctx.beginPath();
      ctx.moveTo(cx + 2, baseY - height * 0.45);
      ctx.bezierCurveTo(cx + width * 0.7, baseY - height * 0.48, cx + width * 1.0, baseY - height * 0.54, cx + width * 1.2, baseY - height * 0.58);
      ctx.stroke();
      ctx.restore();
    }
  }

  ctx.restore();
}

function drawLeaf(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  r: number,
  color: string,
  alpha: number,
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x, y - r);
  ctx.bezierCurveTo(x + r * 0.6, y - r * 0.6, x + r * 0.5, y + r * 0.2, x, y + r * 0.5);
  ctx.bezierCurveTo(x - r * 0.5, y + r * 0.2, x - r * 0.6, y - r * 0.6, x, y - r);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawFlowers(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  colors: TreeColorConfig,
  stage: string,
  elapsed: number,
) {
  const count = stage === "bud" ? 3 : stage === "flowering" ? 6 : 4;
  const flowers: Array<{ x: number; y: number; size: number }> = [];
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 + 0.5;
    const dist = r * 0.55;
    flowers.push({
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist * 0.65,
      size: stage === "bud" ? 3 : 5,
    });
  }

  for (let i = 0; i < flowers.length; i++) {
    const f = flowers[i];
    const fp = prog(elapsed, 350, 700 + i * 80);
    if (fp <= 0) continue;

    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.scale(fp, fp);

    if (stage === "bud") {
      shadow(ctx, "soft");
      ctx.fillStyle = colors.flower;
      ctx.beginPath();
      ctx.ellipse(0, 0, f.size, f.size * 1.3, 0, 0, Math.PI * 2);
      ctx.fill();
      shadow(ctx, "none");
      ctx.fillStyle = "rgba(255,255,255,0.3)";
      ctx.beginPath();
      ctx.ellipse(-1, -1, f.size * 0.4, f.size * 0.5, 0, 0, Math.PI * 2);
      ctx.fill();
    } else {
      // 5 petals
      for (const deg of [0, 72, 144, 216, 288]) {
        const rad = (deg * Math.PI) / 180;
        const pd = 3.5;
        const px = Math.cos(rad) * pd;
        const py = Math.sin(rad) * pd;
        ctx.save();
        ctx.translate(px, py);
        ctx.rotate(rad);
        ctx.fillStyle = colors.flower;
        ctx.beginPath();
        ctx.ellipse(0, 0, 3, 4, 0, 0, Math.PI * 2);
        ctx.fill();
        // petal highlight
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.beginPath();
        ctx.arc(Math.cos(rad) * 0.8, Math.sin(rad) * 0.8 - 0.5, 0.8, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      // center
      ctx.fillStyle = colors.fruit;
      ctx.beginPath();
      ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,0.4)";
      ctx.beginPath();
      ctx.arc(-0.5, -0.5, 0.8, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }

  // fruits (mature only)
  if (stage === "mature") {
    for (let i = 0; i < Math.min(3, flowers.length); i++) {
      const f = flowers[i];
      const fx = f.x + (i % 2 ? 5 : -5);
      const fy = f.y + 7;
      const frp = prog(elapsed, 400, 1100 + i * 120);
      if (frp <= 0) continue;

      ctx.save();
      ctx.translate(fx, fy);
      ctx.scale(frp, frp);

      // fruit gradient
      const fGrad = ctx.createRadialGradient(-1, -1.5, 0, 0, 0, 5.5);
      fGrad.addColorStop(0, rgba(...hexRgb(colors.fruit), 0.9));
      fGrad.addColorStop(1, colors.fruit);
      shadow(ctx, "soft");
      ctx.fillStyle = fGrad;
      ctx.beginPath();
      ctx.arc(0, 0, 5.5, 0, Math.PI * 2);
      ctx.fill();
      shadow(ctx, "none");

      // highlight
      ctx.fillStyle = "rgba(255,255,255,0.35)";
      ctx.beginPath();
      ctx.arc(-1.5, -1.5, 1.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }
}

function drawCanopy(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  colors: TreeColorConfig,
  canopyType: CanopyType,
  stage: string,
  elapsed: number,
  time: number,
  scale: number,
  colorCache: ColorCache,
) {
  // sprout special case
  if (stage === "sprout") {
    const sp = prog(elapsed, 350, 300);
    if (sp > 0) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(sp, sp);
      ctx.translate(-cx, -cy);
      ctx.fillStyle = colors.leaf;
      ctx.beginPath();
      ctx.ellipse(cx - 5, cy, 7, 4, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = colors.leafLight;
      ctx.beginPath();
      ctx.ellipse(cx + 5, cy, 7, 4, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,0.2)";
      ctx.beginPath();
      ctx.ellipse(cx - 5, cy - 0.5, 4, 2, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(cx + 5, cy - 0.5, 4, 2, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    return;
  }

  // canopy shape
  const cp = prog(elapsed, 400, 150);
  if (cp <= 0) return;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.scale(cp, cp);
  ctx.translate(-cx, -cy);

  // main canopy fill with radial gradient
  const leafCol = breatheRgb(colorCache.leaf, time);
  const leafLightCol = breatheRgb(colorCache.leafLight, time);
  const leafDarkCol = breatheRgb(colorCache.leafDark, time);

  const cGrad = ctx.createRadialGradient(
    cx - r * 0.2, cy - r * 0.3, 0,
    cx, cy, r * 0.9,
  );
  cGrad.addColorStop(0, leafLightCol);
  cGrad.addColorStop(0.6, leafCol);
  cGrad.addColorStop(1, leafDarkCol);

  shadow(ctx, "main");
  canopyPath(ctx, canopyType, cx, cy, r, 42);
  ctx.fillStyle = cGrad;
  ctx.fill("evenodd");
  shadow(ctx, "none");

  // highlight overlay
  const hGrad = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.35, 0, cx, cy, r * 0.6);
  hGrad.addColorStop(0, "rgba(255,255,255,0.25)");
  hGrad.addColorStop(1, "rgba(255,255,255,0)");
  canopyPath(ctx, canopyType, cx, cy, r, 42);
  ctx.fillStyle = hGrad;
  ctx.fill("evenodd");

  // individual leaves
  const leafCount = stage === "first_leaf" ? 4 : Math.floor(r / 3.5);
  for (let i = 0; i < leafCount; i++) {
    const angle = (i / leafCount) * Math.PI * 2 + (i % 2) * 0.3;
    const dist = r * (0.25 + (i % 3) * 0.2);
    const lx = cx + Math.cos(angle) * dist;
    const ly = cy + Math.sin(angle) * dist * 0.8;
    const lr = Math.max(4, r / (3.2 + (i % 2)));
    const lp = prog(elapsed, 350, 250 + i * 40);
    const lColor = i % 3 === 0 ? colors.leafLight : colors.leaf;
    drawLeaf(ctx, lx, ly, lr, lColor, lp);
  }

  // flowers / fruits
  if (stage === "flowering" || stage === "bud" || stage === "mature") {
    drawFlowers(ctx, cx, cy, r, colors, stage, elapsed);
  }

  ctx.restore();
}

function drawSeedStage(
  ctx: CanvasRenderingContext2D,
  cx: number,
  baseY: number,
  colors: TreeColorConfig,
  elapsed: number,
) {
  // mound
  const mGrad = ctx.createRadialGradient(cx, baseY - 3, 0, cx, baseY - 2, 16);
  mGrad.addColorStop(0, colors.ground);
  mGrad.addColorStop(1, colors.groundDark);
  ctx.fillStyle = mGrad;
  ctx.beginPath();
  ctx.moveTo(cx - 16, baseY + 1);
  ctx.bezierCurveTo(cx - 12, baseY - 5, cx - 5, baseY - 6, cx, baseY - 5);
  ctx.bezierCurveTo(cx + 5, baseY - 6, cx + 12, baseY - 5, cx + 16, baseY + 1);
  ctx.fill();

  // shadow
  ctx.fillStyle = colors.groundDark;
  ctx.globalAlpha = 0.15;
  ctx.beginPath();
  ctx.ellipse(cx, baseY - 2, 10, 2, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;

  // stem (draw-in)
  const stemP = prog(elapsed, 500, 300);
  if (stemP > 0) {
    ctx.save();
    ctx.setLineDash([30]);
    ctx.lineDashOffset = 30 * (1 - stemP);
    ctx.strokeStyle = colors.leaf;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(cx, baseY - 5);
    ctx.bezierCurveTo(cx + 1, baseY - 10, cx + 1.5, baseY - 12, cx + 1.5, baseY - 16);
    ctx.stroke();
    ctx.restore();
  }

  // left leaf
  const llP = prog(elapsed, 350, 700);
  if (llP > 0) {
    ctx.save();
    ctx.translate(cx + 1.5, baseY - 16);
    ctx.scale(llP, llP);
    ctx.translate(-cx - 1.5, -baseY + 16);
    ctx.fillStyle = colors.leaf;
    ctx.beginPath();
    ctx.moveTo(cx + 1.5, baseY - 16);
    ctx.bezierCurveTo(cx + 5, baseY - 18, cx + 6, baseY - 20, cx + 4, baseY - 20);
    ctx.fill();
    ctx.restore();
  }

  // right leaf
  const rlP = prog(elapsed, 350, 850);
  if (rlP > 0) {
    ctx.save();
    ctx.translate(cx + 1.5, baseY - 16);
    ctx.scale(rlP, rlP);
    ctx.translate(-cx - 1.5, -baseY + 16);
    ctx.fillStyle = colors.leafLight;
    ctx.beginPath();
    ctx.moveTo(cx + 1.5, baseY - 16);
    ctx.bezierCurveTo(cx - 3, baseY - 18, cx - 4, baseY - 20, cx - 2, baseY - 20);
    ctx.fill();
    ctx.restore();
  }

  // highlight
  const hlP = prog(elapsed, 350, 1000);
  if (hlP > 0) {
    ctx.save();
    ctx.globalAlpha = hlP;
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.beginPath();
    ctx.ellipse(cx + 2, baseY - 17.5, 2, 1.2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function drawThrivingGlow(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
) {
  const glowGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 1.8);
  glowGrad.addColorStop(0, "rgba(255,213,79,0.15)");
  glowGrad.addColorStop(1, "rgba(255,213,79,0)");
  ctx.fillStyle = glowGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, r * 1.8, 0, Math.PI * 2);
  ctx.fill();
}

function drawBloomGlow(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  canopyType: CanopyType,
) {
  ctx.save();
  ctx.globalAlpha = 0.25;
  shadow(ctx, "glow", "rgba(255,213,79,0.45)");
  canopyPath(ctx, canopyType, cx, cy, r, 42);
  ctx.fillStyle = "rgba(255,230,100,0.2)";
  ctx.fill();
  shadow(ctx, "none");
  ctx.restore();
}

// ─── Hex → RGB helper ────────────────────────────────────────────────────────

function hexRgb(hex: string): [number, number, number] {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

export function renderTree(ctx: CanvasRenderingContext2D, params: TreeRenderParams): void {
  const { stage, emotion, colors, size, time, mountTime } = params;
  const cfg = STAGE_SIZES[stage] ?? STAGE_SIZES.seed;
  const w = size ?? cfg.width;
  const h = size ? size * (cfg.height / cfg.width) : cfg.height;
  const cx = w / 2;
  const baseY = h - 10;
  const sc = w / cfg.width;
  const trunkH = cfg.trunkH * sc;
  const crownR = cfg.crownR * sc;
  const trunkW = Math.max(3, 6 * sc);
  const crownCy = baseY - trunkH - crownR * 0.4;
  const canopyType = colors.canopyType ?? "cloud";

  const elapsed = time - mountTime;
  const sa = swayAngle(emotion, time);
  const colorCache = buildColorCache(colors);

  // sway (pivot at center, matching CSS default transform-origin)
  ctx.save();
  ctx.translate(w / 2, h / 2);
  ctx.rotate(sa);
  ctx.translate(-w / 2, -h / 2);

  // thriving glow behind tree
  if (emotion === "thriving" && stage !== "seed") {
    drawThrivingGlow(ctx, cx, crownCy, crownR);
  }

  if (stage === "seed") {
    drawSeedStage(ctx, cx, baseY, colors, elapsed);
  } else {
    drawGround(ctx, cx, baseY, colors, elapsed);
    drawTrunk(ctx, cx, baseY, trunkH, trunkW, colors, stage, elapsed, sc);
    drawCanopy(ctx, cx, crownCy, crownR, colors, canopyType, stage, elapsed, time, sc, colorCache);

    // bloom glow overlay for thriving
    if (emotion === "thriving" && crownR > 5) {
      drawBloomGlow(ctx, cx, crownCy, crownR, canopyType);
    }
  }

  ctx.restore();
}
