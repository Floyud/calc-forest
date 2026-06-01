"use client";

const TEACHER_BLOBS = [
  { color: "rgba(90, 158, 78, 0.18)", size: 520, top: "8%", left: "10%", delay: "0s", duration: "22s" },
  { color: "rgba(212, 168, 67, 0.16)", size: 440, top: "55%", right: "5%", delay: "7s", duration: "19s" },
  { color: "rgba(160, 184, 142, 0.20)", size: 380, bottom: "10%", left: "35%", delay: "14s", duration: "25s" },
  { color: "rgba(200, 224, 190, 0.14)", size: 300, top: "30%", right: "30%", delay: "4s", duration: "20s" },
];

const STUDENT_BLOBS = [
  { color: "rgba(122, 154, 113, 0.18)", size: 480, top: "5%", left: "8%", delay: "0s", duration: "21s" },
  { color: "rgba(107, 140, 168, 0.15)", size: 420, top: "50%", right: "8%", delay: "6s", duration: "24s" },
  { color: "rgba(194, 212, 184, 0.20)", size: 360, bottom: "15%", left: "30%", delay: "12s", duration: "18s" },
  { color: "rgba(224, 232, 218, 0.13)", size: 280, top: "35%", right: "25%", delay: "3s", duration: "22s" },
];

type BlobDef = { color: string; size: number; delay: string; duration: string } & (
  | { top?: string; bottom?: string; left?: string; right?: string }
);

function Blob({ color, size, delay, duration, ...pos }: BlobDef) {
  const position: Record<string, string> = {};
  for (const [k, v] of Object.entries(pos)) {
    if (typeof v === "string") position[k] = v;
  }

  return (
    <span
      className="blob-float absolute rounded-full"
      style={{
        width: size,
        height: size,
        backgroundColor: color,
        filter: "blur(100px)",
        animationDelay: delay,
        animationDuration: duration,
        ...position,
      }}
    />
  );
}

export function BackgroundBlobs({ variant }: { variant: "teacher" | "student" }) {
  const blobs = variant === "teacher" ? TEACHER_BLOBS : STUDENT_BLOBS;

  return (
    <div
      className="fixed inset-0 overflow-hidden pointer-events-none"
      style={{ zIndex: 0 }}
      aria-hidden
    >
      {blobs.map((b, i) => (
        <Blob key={i} {...b} />
      ))}
    </div>
  );
}
