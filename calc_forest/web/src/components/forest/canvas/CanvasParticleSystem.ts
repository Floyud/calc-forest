import type { EmotionState } from "@/lib/types";

export interface ParticleConfig {
  cx: number;
  cy: number;
  width: number;
  height: number;
  color: string;
  intensity: number;
  compact?: boolean;
}

type PKind = "sparkle" | "butterfly" | "heart" | "leaf" | "rain" | "mist" | "firefly" | "growth_pulse";

interface Particle {
  kind: PKind;
  x: number;
  y: number;
  startX: number;
  startY: number;
  life: number;
  maxLife: number;
  delay: number;
  size: number;
  rotation: number;
  rotationSpeed: number;
  color: string;
  driftX: number;
  driftY: number;
  wingMain: string;
  wingAccent: string;
  phase: number;
  // firefly-specific
  glowRadius: number;
  pulsePhase: number;
  pulseSpeed: number;
  trailX: number[];
  trailY: number[];
  // growth_pulse-specific
  pulseRadius: number;
  maxPulseRadius: number;
  pulseColor: string;
  // sparkle enhancement
  twinkleTriggered: boolean;
}

const BUTTERFLY_PALETTES = [
  { main: "#FF6B9D", accent: "#FF9EC5" },
  { main: "#B388FF", accent: "#D1B3FF" },
  { main: "#4DD0E1", accent: "#80DEEA" },
];

const LEAF_COLORS = ["#E8A840", "#D4843A", "#C47232", "#B8922A"];

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function makeSparkle(cfg: ParticleConfig, spread: number): Particle {
  return {
    kind: "sparkle",
    x: cfg.cx + rand(-0.4, 0.4) * spread,
    y: cfg.cy + rand(0, 20),
    startX: 0, startY: 0,
    life: -rand(0, 3),
    maxLife: rand(2, 4),
    delay: 0,
    size: rand(2.5, 5),
    rotation: 0,
    rotationSpeed: 0,
    color: Math.random() > 0.5 ? "#FFD700" : cfg.color,
    driftX: 0, driftY: 0,
    wingMain: "", wingAccent: "",
    phase: rand(0, Math.PI * 2),
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeButterfly(cfg: ParticleConfig): Particle {
  const pal = BUTTERFLY_PALETTES[Math.floor(Math.random() * BUTTERFLY_PALETTES.length)];
  return {
    kind: "butterfly",
    x: cfg.cx, y: cfg.cy,
    startX: cfg.cx, startY: cfg.cy,
    life: 0,
    maxLife: 999,
    delay: 0,
    size: 1,
    rotation: 0,
    rotationSpeed: 0,
    color: "",
    driftX: rand(18, 28), driftY: 0,
    wingMain: pal.main, wingAccent: pal.accent,
    phase: rand(0, Math.PI * 2),
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeHeart(cfg: ParticleConfig): Particle {
  return {
    kind: "heart",
    x: cfg.cx + rand(-0.25, 0.25) * cfg.width,
    y: cfg.cy + rand(0, 10),
    startX: 0, startY: 0,
    life: -rand(1, 5),
    maxLife: rand(3, 5),
    delay: 0,
    size: rand(2, 4),
    rotation: 0, rotationSpeed: 0,
    color: "#FF6B9D",
    driftX: 0, driftY: 0,
    wingMain: "", wingAccent: "",
    phase: 0,
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeLeaf(cfg: ParticleConfig): Particle {
  return {
    kind: "leaf",
    x: cfg.cx + rand(-0.2, 0.2) * cfg.width,
    y: cfg.cy + rand(0, 10),
    startX: 0, startY: 0,
    life: -rand(2, 7),
    maxLife: rand(3, 5),
    delay: 0,
    size: rand(3, 6),
    rotation: rand(0, 360),
    rotationSpeed: rand(60, 120),
    color: LEAF_COLORS[Math.floor(Math.random() * LEAF_COLORS.length)],
    driftX: rand(-20, 20), driftY: 0,
    wingMain: "", wingAccent: "",
    phase: 0,
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeRain(cfg: ParticleConfig): Particle {
  return {
    kind: "rain",
    x: cfg.cx + rand(-0.45, 0.45) * cfg.width,
    y: -8,
    startX: 0, startY: 0,
    life: -rand(0, 2),
    maxLife: rand(0.5, 0.9),
    delay: 0,
    size: 1,
    rotation: 0, rotationSpeed: 0,
    color: cfg.color,
    driftX: rand(-1, 1), driftY: 0,
    wingMain: "", wingAccent: "",
    phase: 0,
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeMist(cfg: ParticleConfig): Particle {
  return {
    kind: "mist",
    x: cfg.cx + rand(-0.25, 0.25) * cfg.width,
    y: cfg.cy + 5 + rand(0, 15),
    startX: 0, startY: 0,
    life: -rand(0, 4),
    maxLife: rand(4, 6),
    delay: 0,
    size: 1,
    rotation: 0, rotationSpeed: 0,
    color: "",
    driftX: 0, driftY: 0,
    wingMain: "", wingAccent: "",
    phase: 0,
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeFirefly(cfg: ParticleConfig): Particle {
  const startX = cfg.cx + rand(-0.35, 0.35) * cfg.width;
  const startY = cfg.cy + rand(-15, 5);
  return {
    kind: "firefly",
    x: startX, y: startY,
    startX, startY,
    life: -rand(0, 2),
    maxLife: rand(6, 10),
    delay: 0,
    size: rand(2, 3.5),
    rotation: 0, rotationSpeed: 0,
    color: "",
    driftX: rand(12, 25),
    driftY: rand(8, 18),
    wingMain: "", wingAccent: "",
    phase: rand(0, Math.PI * 2),
    glowRadius: rand(10, 18),
    pulsePhase: rand(0, Math.PI * 2),
    pulseSpeed: rand(2.5, 3.5),
    trailX: [startX, startX, startX],
    trailY: [startY, startY, startY],
    pulseRadius: 0, maxPulseRadius: 0, pulseColor: "",
    twinkleTriggered: false,
  };
}

function makeGrowthPulse(cx: number, cy: number, accentColor: string, maxRadius: number): Particle {
  return {
    kind: "growth_pulse",
    x: cx, y: cy,
    startX: cx, startY: cy,
    life: 0,
    maxLife: 1.8,
    delay: 0,
    size: 1,
    rotation: 0, rotationSpeed: 0,
    color: "",
    driftX: 0, driftY: 0,
    wingMain: "", wingAccent: "",
    phase: 0,
    glowRadius: 0, pulsePhase: 0, pulseSpeed: 0, trailX: [], trailY: [],
    pulseRadius: 0,
    maxPulseRadius: maxRadius,
    pulseColor: accentColor,
    twinkleTriggered: false,
  };
}

function resetParticle(p: Particle, cfg: ParticleConfig): void {
  switch (p.kind) {
    case "sparkle":
      p.x = cfg.cx + rand(-0.4, 0.4) * cfg.width;
      p.y = cfg.cy + rand(0, 20);
      p.life = 0;
      p.maxLife = rand(2, 4);
      p.size = rand(2.5, 5);
      break;
    case "heart":
      p.x = cfg.cx + rand(-0.25, 0.25) * cfg.width;
      p.y = cfg.cy + rand(0, 10);
      p.life = 0;
      p.maxLife = rand(3, 5);
      p.size = rand(2, 4);
      break;
    case "leaf":
      p.x = cfg.cx + rand(-0.2, 0.2) * cfg.width;
      p.y = cfg.cy + rand(0, 10);
      p.life = 0;
      p.maxLife = rand(3, 5);
      p.rotation = rand(0, 360);
      p.driftX = rand(-20, 20);
      break;
    case "rain":
      p.x = cfg.cx + rand(-0.45, 0.45) * cfg.width;
      p.y = -8;
      p.life = 0;
      p.maxLife = rand(0.5, 0.9);
      break;
    case "mist":
      p.x = cfg.cx + rand(-0.25, 0.25) * cfg.width;
      p.y = cfg.cy + 5 + rand(0, 15);
      p.life = 0;
      p.maxLife = rand(4, 6);
      break;
    case "firefly":
      p.startX = cfg.cx + rand(-0.35, 0.35) * cfg.width;
      p.startY = cfg.cy + rand(-15, 5);
      p.x = p.startX;
      p.y = p.startY;
      p.life = 0;
      p.maxLife = rand(6, 10);
      p.trailX = [p.x, p.x, p.x];
      p.trailY = [p.y, p.y, p.y];
      break;
    default: break;
  }
}

export class ParticleSystem {
  private particles: Particle[] = [];
  private emotion: EmotionState;
  private config: ParticleConfig;

  constructor(emotion: EmotionState, config: ParticleConfig) {
    this.emotion = emotion;
    this.config = config;
    this.spawn();
  }

  private spawn() {
    const { cx, cy, width, color } = this.config;
    switch (this.emotion) {
      case "thriving":
        for (let i = 0; i < 3; i++) this.particles.push(makeSparkle(this.config, width * 0.8));
        this.particles.push(makeButterfly(this.config));
        this.particles.push(makeHeart(this.config));
        for (let i = 0; i < 5; i++) this.particles.push(makeFirefly(this.config));
        break;
      case "happy":
        for (let i = 0; i < 2; i++) this.particles.push(makeSparkle(this.config, width * 0.5));
        for (let i = 0; i < 3; i++) this.particles.push(makeFirefly(this.config));
        break;
      case "wilting":
        for (let i = 0; i < 4; i++) this.particles.push(makeLeaf(this.config));
        for (let i = 0; i < 1; i++) this.particles.push(makeFirefly(this.config));
        break;
      case "struggling": {
        const isCompact = this.config.compact ?? false;
        const rainCount = isCompact ? 3 : 8;
        const mistCount = isCompact ? 1 : 3;
        for (let i = 0; i < rainCount; i++) this.particles.push(makeRain(this.config));
        for (let i = 0; i < mistCount; i++) this.particles.push(makeMist(this.config));
        break;
      }
      default: break;
    }
    void cx; void cy; void color;
  }

  update(dt: number) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.life += dt;

      if (p.kind === "growth_pulse") {
        if (p.life >= p.maxLife) {
          this.particles.splice(i, 1);
          continue;
        }
        const t = p.life / p.maxLife;
        p.pulseRadius = p.maxPulseRadius * t;
        continue;
      }

      if (p.life >= p.maxLife) {
        resetParticle(p, this.config);
      }
      if (p.life < 0) continue;

      switch (p.kind) {
        case "sparkle": {
          const t = p.life / p.maxLife;
          p.y = p.y - dt * 30 * (1 - t);
          break;
        }
        case "heart": {
          const t = p.life / p.maxLife;
          p.y = p.y - dt * 20 * (1 - t);
          break;
        }
        case "leaf": {
          const t = p.life / p.maxLife;
          p.y += dt * 20;
          p.x += Math.sin(p.life * 2 + p.phase) * dt * 5;
          p.rotation += p.rotationSpeed * dt;
          break;
        }
        case "rain": {
          p.y += dt * 160;
          p.x += p.driftX * dt;
          break;
        }
        case "firefly": {
          p.trailX.push(p.x);
          p.trailY.push(p.y);
          if (p.trailX.length > 3) { p.trailX.shift(); p.trailY.shift(); }
          p.x = p.startX + Math.sin(p.life * 0.7 + p.phase) * p.driftX;
          p.y = p.startY + Math.cos(p.life * 0.5 + p.phase * 1.3) * p.driftY;
          p.pulsePhase += dt * p.pulseSpeed;
          break;
        }
        case "butterfly":
        case "mist":
          break;
      }
    }
  }

  render(ctx: CanvasRenderingContext2D, time: number) {
    for (const p of this.particles) {
      if (p.life < 0) continue;
      const t = p.maxLife > 900 ? 0.5 : p.life / p.maxLife;

      switch (p.kind) {
        case "sparkle": this.drawSparkle(ctx, p, t, time); break;
        case "butterfly": this.drawButterfly(ctx, p, time); break;
        case "heart": this.drawHeart(ctx, p, t); break;
        case "leaf": this.drawLeaf(ctx, p, t); break;
        case "rain": this.drawRain(ctx, p, t); break;
        case "mist": this.drawMist(ctx, p, t); break;
        case "firefly": this.drawFirefly(ctx, p, t); break;
        case "growth_pulse": this.drawGrowthPulse(ctx, p); break;
      }
    }
  }

  private drawSparkle(ctx: CanvasRenderingContext2D, p: Particle, t: number, time: number) {
    const twinkleRate = 3 + p.phase;
    const twinkleFlash = Math.pow(Math.max(0, Math.sin(time * 0.001 * twinkleRate)), 12);
    const fadeOpacity = t < 0.15 ? t / 0.15 : Math.max(0, 1 - (t - 0.15) / 0.85);
    const opacity = Math.min(1, fadeOpacity * 0.85 + twinkleFlash * 0.9);
    const sc = t < 0.15 ? t / 0.15 * 1.2 : Math.max(0.3, 1 - t * 0.7);

    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.scale(sc, sc);

    if (twinkleFlash > 0.3) {
      const glowR = p.size * 3;
      const glow = ctx.createRadialGradient(0, 0, 0, 0, 0, glowR);
      const isGold = p.color === "#FFD700";
      const glowColor = isGold ? "255,215,0" : "255,255,255";
      glow.addColorStop(0, `rgba(${glowColor},${twinkleFlash * 0.4})`);
      glow.addColorStop(1, `rgba(${glowColor},0)`);
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(0, 0, glowR, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.globalAlpha = opacity;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    const s = p.size;
    const inner = s * 0.3;
    ctx.moveTo(0, -s);
    ctx.bezierCurveTo(inner * 0.4, -inner * 0.4, inner * 0.4, -inner * 0.4, inner, -inner * 0.2);
    ctx.bezierCurveTo(inner * 0.4, inner * 0.1, inner * 0.4, inner * 0.2, s * 0.1, inner);
    ctx.bezierCurveTo(inner * 0.1, inner * 0.4, 0, inner * 0.5, 0, s);
    ctx.bezierCurveTo(-inner * 0.1, inner * 0.5, -inner * 0.1, inner * 0.4, -s * 0.1, inner);
    ctx.bezierCurveTo(-inner * 0.4, inner * 0.2, -inner * 0.4, inner * 0.1, -inner, -inner * 0.2);
    ctx.bezierCurveTo(-inner * 0.4, -inner * 0.4, -inner * 0.4, -inner * 0.4, 0, -s);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  private drawButterfly(ctx: CanvasRenderingContext2D, p: Particle, time: number) {
    const elapsed = time * 0.001;
    const bx = p.startX + Math.cos(elapsed * 1.2 + p.phase) * p.driftX;
    const by = p.startY + Math.sin(elapsed * 1.8 + p.phase) * (p.driftX * 0.5);
    const wingFlap = 0.3 + Math.abs(Math.sin(time * 0.008 + p.phase)) * 0.7;

    ctx.save();
    ctx.translate(bx, by);
    ctx.globalAlpha = 0.85;

    // left wing
    ctx.fillStyle = p.wingMain;
    ctx.beginPath();
    ctx.ellipse(-3, 0, 5 * wingFlap, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    // left wing highlight
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.beginPath();
    ctx.arc(-3 - 1, -2, 1.5, 0, Math.PI * 2);
    ctx.fill();

    // right wing
    ctx.fillStyle = p.wingMain;
    ctx.beginPath();
    ctx.ellipse(3, 0, 5 * wingFlap, 7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.beginPath();
    ctx.arc(3 + 1, -2, 1.5, 0, Math.PI * 2);
    ctx.fill();

    // body
    ctx.fillStyle = "#4A3728";
    ctx.beginPath();
    ctx.ellipse(0, 0, 1.5, 4, 0, 0, Math.PI * 2);
    ctx.fill();

    // antennae
    ctx.strokeStyle = "#4A3728";
    ctx.lineWidth = 0.6;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(-1, -3);
    ctx.lineTo(-3, -7);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(1, -3);
    ctx.lineTo(3, -7);
    ctx.stroke();
    ctx.fillStyle = p.wingMain;
    ctx.beginPath();
    ctx.arc(-3, -7, 0.8, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(3, -7, 0.8, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  private drawHeart(ctx: CanvasRenderingContext2D, p: Particle, t: number) {
    const opacity = t < 0.15 ? t / 0.15 : Math.max(0, 1 - (t - 0.15) / 0.85);
    const sc = t < 0.15 ? t / 0.15 : Math.max(0.3, 1 - t * 0.7);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.scale(sc * (p.size / 4), sc * (p.size / 4));
    ctx.globalAlpha = opacity * 0.7;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.moveTo(5, 8);
    ctx.bezierCurveTo(5, 8, 1, 5.5, 1, 3);
    ctx.bezierCurveTo(1, 1.5, 2.5, 0.5, 3.5, 1.5);
    ctx.bezierCurveTo(4, 2, 4.5, 2.5, 5, 3.5);
    ctx.bezierCurveTo(5.5, 2.5, 6, 2, 6.5, 1.5);
    ctx.bezierCurveTo(7.5, 0.5, 9, 1.5, 9, 3);
    ctx.bezierCurveTo(9, 5.5, 5, 8, 5, 8);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  private drawLeaf(ctx: CanvasRenderingContext2D, p: Particle, t: number) {
    const opacity = Math.max(0, 0.7 * (1 - t));
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate((p.rotation * Math.PI) / 180);
    ctx.globalAlpha = opacity;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    const r = p.size;
    ctx.moveTo(0, -r);
    ctx.bezierCurveTo(r * 0.6, -r * 0.6, r * 0.5, r * 0.2, 0, r * 0.5);
    ctx.bezierCurveTo(-r * 0.5, r * 0.2, -r * 0.6, -r * 0.6, 0, -r);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  private drawRain(ctx: CanvasRenderingContext2D, p: Particle, t: number) {
    const opacity = t < 0.1 ? t / 0.1 * 0.4 : t > 0.9 ? 0.3 * (1 - (t - 0.9) / 0.1) : 0.4;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.globalAlpha = opacity;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.moveTo(3, 0);
    ctx.bezierCurveTo(5, 3, 5, 5, 5, 6.5);
    ctx.bezierCurveTo(5, 8.5, 4, 10, 3, 10);
    ctx.bezierCurveTo(2, 10, 1, 8.5, 1, 6.5);
    ctx.bezierCurveTo(1, 5, 1, 3, 3, 0);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.beginPath();
    ctx.ellipse(2.2, 5, 0.6, 1.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  private drawMist(ctx: CanvasRenderingContext2D, p: Particle, t: number) {
    const opacity = t < 0.2 ? t / 0.2 * 0.35 : t > 0.8 ? 0.35 * (1 - (t - 0.8) / 0.2) : 0.35;
    const dx = Math.sin(t * Math.PI * 2) * 10;
    ctx.save();
    ctx.translate(p.x - 20 + dx, p.y);
    ctx.globalAlpha = opacity;
    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(0, 8);
    ctx.bezierCurveTo(5, 4, 10, 6, 15, 7);
    ctx.bezierCurveTo(20, 8, 25, 5, 30, 6);
    ctx.bezierCurveTo(35, 7, 38, 5, 40, 7);
    ctx.stroke();
    ctx.strokeStyle = "rgba(255,255,255,0.2)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(2, 10);
    ctx.bezierCurveTo(8, 7, 14, 9, 20, 8);
    ctx.bezierCurveTo(26, 7, 32, 9, 38, 8);
    ctx.stroke();
    ctx.restore();
  }

  private drawFirefly(ctx: CanvasRenderingContext2D, p: Particle, t: number) {
    const fadeIn = t < 0.1 ? t / 0.1 : 1;
    const fadeOut = t > 0.85 ? (1 - t) / 0.15 : 1;
    const baseAlpha = fadeIn * fadeOut;

    const pulse = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(p.pulsePhase));
    const alpha = baseAlpha * pulse;

    ctx.save();

    for (let i = 0; i < p.trailX.length; i++) {
      const trailAlpha = alpha * 0.15 * (i + 1) / p.trailX.length;
      const trailR = p.glowRadius * 0.4 * (i + 1) / p.trailX.length;
      const tg = ctx.createRadialGradient(p.trailX[i], p.trailY[i], 0, p.trailX[i], p.trailY[i], trailR);
      tg.addColorStop(0, `rgba(200,230,100,${trailAlpha})`);
      tg.addColorStop(1, `rgba(180,220,80,0)`);
      ctx.fillStyle = tg;
      ctx.beginPath();
      ctx.arc(p.trailX[i], p.trailY[i], trailR, 0, Math.PI * 2);
      ctx.fill();
    }

    const glowR = p.glowRadius * (0.7 + 0.3 * pulse);
    const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowR);
    glow.addColorStop(0, `rgba(200,230,100,${alpha * 0.7})`);
    glow.addColorStop(0.3, `rgba(190,225,90,${alpha * 0.4})`);
    glow.addColorStop(0.6, `rgba(180,220,80,${alpha * 0.15})`);
    glow.addColorStop(1, `rgba(180,220,80,0)`);
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
    ctx.fill();

    ctx.globalAlpha = alpha;
    ctx.fillStyle = `rgba(255,255,200,${alpha})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size * 0.6, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  private drawGrowthPulse(ctx: CanvasRenderingContext2D, p: Particle) {
    const t = p.life / p.maxLife;
    const alpha = Math.max(0, 1 - t);
    if (alpha <= 0) return;

    ctx.save();
    ctx.translate(p.x, p.y);

    const outerRing = ctx.createRadialGradient(0, 0, p.pulseRadius * 0.85, 0, 0, p.pulseRadius);
    outerRing.addColorStop(0, `rgba(${p.pulseColor},0)`);
    outerRing.addColorStop(0.5, `rgba(${p.pulseColor},${alpha * 0.3})`);
    outerRing.addColorStop(1, `rgba(${p.pulseColor},0)`);
    ctx.fillStyle = outerRing;
    ctx.beginPath();
    ctx.arc(0, 0, p.pulseRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = `rgba(${p.pulseColor},${alpha * 0.7})`;
    ctx.lineWidth = Math.max(0.5, 3 * (1 - t));
    ctx.beginPath();
    ctx.arc(0, 0, p.pulseRadius, 0, Math.PI * 2);
    ctx.stroke();

    if (t < 0.3) {
      const innerAlpha = (1 - t / 0.3) * 0.4;
      ctx.strokeStyle = `rgba(255,255,255,${innerAlpha})`;
      ctx.lineWidth = Math.max(0.3, 1.5 * (1 - t));
      ctx.beginPath();
      ctx.arc(0, 0, p.pulseRadius * 0.6, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
  }

  emitGrowthPulse(accentColor: string, maxRadius?: number) {
    const { cx, cy } = this.config;
    const r = maxRadius ?? Math.max(this.config.width, this.config.height) * 0.45;
    this.particles.push(makeGrowthPulse(cx, cy, accentColor, r));
  }

  updateEmotion(emotion: EmotionState, config: ParticleConfig) {
    if (emotion === this.emotion) return;
    this.emotion = emotion;
    this.config = config;
    this.particles = [];
    this.spawn();
  }
}
