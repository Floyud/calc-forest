"use client";

/**
 * Global SVG defs rendered ONCE at app layout level.
 * Contains static filters and base gradients shared by all tree instances.
 * Color-dependent gradients are still rendered per-tree (inline).
 */
export function TreeDefs() {
  return (
    <svg
      aria-hidden="true"
      style={{
        position: "absolute",
        width: 0,
        height: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      <defs>
        {/* Reusable drop shadow — replaces per-tree feDropShadow */}
        <filter id="tree-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(0,0,0,0.12)" />
        </filter>
        {/* Soft shadow for small elements */}
        <filter id="tree-soft-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor="rgba(0,0,0,0.08)" />
        </filter>
        {/* Canopy highlight (color-independent white overlay) */}
        <radialGradient id="canopy-highlight" cx="30%" cy="25%" r="50%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.25)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0)" />
        </radialGradient>
        {/* Thriving glow — always available, no conditional rendering needed */}
        <radialGradient id="thriving-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(255,213,79,0.15)" />
          <stop offset="100%" stopColor="rgba(255,213,79,0)" />
        </radialGradient>
      </defs>
    </svg>
  );
}
