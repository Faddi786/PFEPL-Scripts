import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

type Phase = "sphere" | "success";

type Props = {
  onComplete: () => void;
};

const SPHERE_SIZE = 193;
const BOX_MAX_WIDTH = 204;
const TICK_SIZE = 94;
const PROJ_SCALE = 59;
const RING_RADIUS = 63;

const LAT_STEPS = 30;
const LON_STEPS = 44;

type ProjectedNode = {
  px: number;
  py: number;
  z: number;
};

function waveDisplacement(lat: number, lon: number, time: number) {
  return (
    Math.sin(lat * 7 + time * 1.85) * 0.15 +
    Math.sin(lon * 9 - time * 1.35) * 0.13 +
    Math.sin(lat * 2 + lon * 3 + time * 2.1) * 0.1 +
    Math.sin(lat * 11 - lon * 5 + time * 1.55) * 0.08
  );
}

function projectSphereGrid(time: number, cx: number, cy: number, floatY: number, projScale: number) {
  const rot = time * 0.38;
  const cosR = Math.cos(rot);
  const sinR = Math.sin(rot);
  const grid: ProjectedNode[][] = [];

  for (let i = 0; i <= LAT_STEPS; i += 1) {
    grid[i] = [];
    const lat = (i / LAT_STEPS) * Math.PI - Math.PI / 2;

    for (let j = 0; j <= LON_STEPS; j += 1) {
      const lon = (j / LON_STEPS) * Math.PI * 2;
      const wave = waveDisplacement(lat, lon, time);
      const r = 1 + wave;

      const x0 = r * Math.cos(lat) * Math.cos(lon);
      const y0 = r * Math.sin(lat);
      const z0 = r * Math.cos(lat) * Math.sin(lon);

      const x = x0 * cosR - z0 * sinR;
      const z = x0 * sinR + z0 * cosR;
      const depth = 2.45 + z;
      const scale = projScale / depth;

      grid[i][j] = {
        px: cx + x * scale,
        py: cy + floatY + y0 * scale,
        z,
      };
    }
  }

  return grid;
}

function ParticleSphere({ running }: { running: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!running) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = SPHERE_SIZE;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    let frameId = 0;

    const draw = (now: number) => {
      const time = now * 0.001;
      const cx = size / 2;
      const cy = size / 2;
      const floatY = Math.sin(time * 1.1) * 2;
      const projScale = PROJ_SCALE;
      const ringRadius = RING_RADIUS;

      ctx.clearRect(0, 0, size, size);

      const grid = projectSphereGrid(time, cx, cy, floatY, projScale);

      type Segment = { x1: number; y1: number; x2: number; y2: number; z: number };
      const segments: Segment[] = [];

      for (let i = 0; i <= LAT_STEPS; i += 1) {
        for (let j = 0; j <= LON_STEPS; j += 1) {
          const a = grid[i][j];
          if (j < LON_STEPS) {
            const b = grid[i][j + 1];
            segments.push({ x1: a.px, y1: a.py, x2: b.px, y2: b.py, z: (a.z + b.z) / 2 });
          }
          if (i < LAT_STEPS) {
            const b = grid[i + 1][j];
            segments.push({ x1: a.px, y1: a.py, x2: b.px, y2: b.py, z: (a.z + b.z) / 2 });
          }
        }
      }

      segments.sort((left, right) => left.z - right.z);

      for (const seg of segments) {
        const depth = (seg.z + 1) / 2;
        if (depth < 0.18) continue;
        ctx.strokeStyle = `rgba(72, 198, 255, ${0.14 + depth * 0.4})`;
        ctx.lineWidth = 0.65;
        ctx.beginPath();
        ctx.moveTo(seg.x1, seg.y1);
        ctx.lineTo(seg.x2, seg.y2);
        ctx.stroke();
      }

      const nodes: ProjectedNode[] = [];
      for (let i = 0; i <= LAT_STEPS; i += 1) {
        for (let j = 0; j <= LON_STEPS; j += 1) {
          nodes.push(grid[i][j]);
        }
      }
      nodes.sort((a, b) => a.z - b.z);

      for (const node of nodes) {
        const depth = (node.z + 1) / 2;
        if (depth < 0.12) continue;

        const radius = 0.55 + depth * 0.95;
        const alpha = 0.45 + depth * 0.55;

        ctx.fillStyle = `rgba(125, 211, 252, ${alpha})`;
        ctx.beginPath();
        ctx.arc(node.px, node.py, radius, 0, Math.PI * 2);
        ctx.fill();

        if (depth > 0.72) {
          ctx.fillStyle = "rgba(191, 233, 255, 0.98)";
          ctx.beginPath();
          ctx.arc(node.px, node.py, radius * 0.45, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.strokeStyle = "rgba(96, 200, 255, 0.62)";
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.arc(cx, cy + floatY, ringRadius, 0, Math.PI * 2);
      ctx.stroke();

      frameId = window.requestAnimationFrame(draw);
    };

    frameId = window.requestAnimationFrame(draw);

    return () => window.cancelAnimationFrame(frameId);
  }, [running]);

  return <canvas ref={canvasRef} className="h-full w-full" aria-hidden />;
}

export default function MobileAuthSuccessOverlay({ onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>("sphere");

  useEffect(() => {
    const successTimer = window.setTimeout(() => setPhase("success"), 1000);
    const completeTimer = window.setTimeout(() => onComplete(), 2000);

    return () => {
      window.clearTimeout(successTimer);
      window.clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center px-6">
      <motion.div
        initial={{ scale: 0.94, opacity: 0, y: 6 }}
        animate={{ scale: 1, opacity: 1, y: [0, -3, 0] }}
        transition={{
          opacity: { duration: 0.3 },
          scale: { duration: 0.35, ease: [0.4, 0, 0.2, 1] },
          y: { duration: 3.2, repeat: Infinity, ease: "easeInOut" },
        }}
        className="pointer-events-auto flex w-full flex-col items-center rounded-[1.75rem] bg-black px-3 py-5 shadow-[0_20px_50px_rgba(0,0,0,0.35)] ring-1 ring-white/10"
        style={{ maxWidth: BOX_MAX_WIDTH }}
      >
        <div
          className="relative flex items-center justify-center"
          style={{ width: SPHERE_SIZE, height: SPHERE_SIZE }}
        >
          <AnimatePresence mode="wait">
            {phase === "sphere" ? (
              <motion.div
                key="sphere"
                initial={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="absolute inset-0 flex items-center justify-center"
              >
                <ParticleSphere running />
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.75 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 360, damping: 24 }}
                className="flex items-center justify-center rounded-full bg-emerald-500 shadow-[0_0_24px_rgba(34,197,94,0.45)]"
                style={{ width: TICK_SIZE, height: TICK_SIZE }}
              >
                <svg
                  viewBox="0 0 24 24"
                  className="shrink-0"
                  style={{ width: TICK_SIZE * 0.56, height: TICK_SIZE * 0.56 }}
                  aria-hidden
                >
                  <path
                    d="M6 12.5 10 16.5 18 8.5"
                    fill="none"
                    stroke="white"
                    strokeWidth="2.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
