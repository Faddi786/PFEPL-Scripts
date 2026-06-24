import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Download, Loader2, Play, Radar } from "lucide-react";
import WorkflowStepper from "../WorkflowStepper";
import AnomalyPipelineMap from "./AnomalyPipelineMap";
import {
  RECORD_MAP_CHECKS,
  VARIANCE_BAND_COLORS,
  type AnomalyPipelinePhase,
  type VarianceBand,
} from "./anomalyPipelineData";
import { downloadAnomalyExportBundle } from "../../lib/anomalyExport";

const STEPS = [
  "Scheduled run",
  "Area compare",
  "Variance bands",
  "Record-map checks",
  "Persist & dashboard",
];

type CheckStatus = "pending" | "running" | "done" | "flagged";

export default function AnomalyPipelineFlow() {
  const [step, setStep] = useState(0);
  const [phase, setPhase] = useState<AnomalyPipelinePhase>("idle");
  const [bandOpacity, setBandOpacity] = useState(0);
  const [running, setRunning] = useState(false);
  const [checks, setChecks] = useState<CheckStatus[]>(RECORD_MAP_CHECKS.map(() => "pending"));
  const [runId, setRunId] = useState(0);
  const [bandFilter, setBandFilter] = useState<VarianceBand | null>(null);
  const [highlightedParcelIndex, setHighlightedParcelIndex] = useState<number | null>(null);
  const [checkFocus, setCheckFocus] = useState<{ checkId: string; cycleIndex: number } | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const fadeFrameRef = useRef<number | null>(null);
  const timersRef = useRef<number[]>([]);

  const analysisComplete = phase === "complete" && step >= STEPS.length;

  function clearTimers() {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
    if (fadeFrameRef.current !== null) {
      window.cancelAnimationFrame(fadeFrameRef.current);
      fadeFrameRef.current = null;
    }
  }

  function schedule(fn: () => void, delay: number) {
    const id = window.setTimeout(fn, delay);
    timersRef.current.push(id);
  }

  function animateBandFade() {
    const start = performance.now();
    const duration = 2000;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      setBandOpacity(progress);
      if (progress < 1) {
        fadeFrameRef.current = window.requestAnimationFrame(tick);
      }
    };

    fadeFrameRef.current = window.requestAnimationFrame(tick);
  }

  function runChecksSequentially() {
    RECORD_MAP_CHECKS.forEach((check, index) => {
      schedule(() => {
        setChecks((prev) => prev.map((status, i) => (i === index ? "running" : status)));
      }, index * 450);

      schedule(() => {
        const flagged = check.flaggedParcelIndices.length > 0;
        setChecks((prev) => prev.map((status, i) => (i === index ? (flagged ? "flagged" : "done") : status)));
      }, index * 450 + 320);
    });
  }

  function toggleBandFilter(band: VarianceBand) {
    setBandFilter((current) => (current === band ? null : band));
    setCheckFocus(null);
    setHighlightedParcelIndex(null);
  }

  function focusCheckParcel(checkId: string) {
    const check = RECORD_MAP_CHECKS.find((item) => item.id === checkId);
    if (!check || check.flaggedParcelIndices.length === 0) return;

    const nextCycle =
      checkFocus?.checkId === checkId
        ? (checkFocus.cycleIndex + 1) % check.flaggedParcelIndices.length
        : 0;
    const parcelIndex = check.flaggedParcelIndices[nextCycle];

    setCheckFocus({ checkId, cycleIndex: nextCycle });
    setBandFilter(null);
    setHighlightedParcelIndex(parcelIndex);
  }

  function runPipeline() {
    clearTimers();
    setRunId((id) => id + 1);
    setRunning(true);
    setStep(0);
    setPhase("satellite");
    setBandOpacity(0);
    setChecks(RECORD_MAP_CHECKS.map(() => "pending"));
    setBandFilter(null);
    setCheckFocus(null);
    setHighlightedParcelIndex(null);
    setExportMessage(null);

    schedule(() => {
      setStep(0);
      setPhase("digitized");
    }, 1400);

    schedule(() => {
      setStep(1);
      setPhase("comparing");
    }, 2800);

    schedule(() => {
      setStep(2);
      setPhase("bands");
      animateBandFade();
    }, 4200);

    schedule(() => {
      setPhase("boundary");
    }, 6400);

    schedule(() => {
      setStep(3);
      runChecksSequentially();
    }, 7200);

    schedule(() => {
      setStep(4);
      setPhase("complete");
    }, 9800);

    schedule(() => {
      setStep(STEPS.length);
      setRunning(false);
    }, 11200);
  }

  function handleExport() {
    setExportMessage("Downloading export bundle…");
    downloadAnomalyExportBundle();
    window.setTimeout(() => setExportMessage(null), 3500);
  }

  useEffect(() => () => clearTimers(), []);

  const canFilterBands = phase === "bands" || phase === "boundary" || phase === "complete";

  return (
    <div className="space-y-4">
      <WorkflowStepper steps={STEPS} activeStep={step} />

      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-[#1A1A1A]">Variance analysis map</h3>
            </div>
            <button
              type="button"
              onClick={runPipeline}
              disabled={running}
              className="inline-flex items-center gap-1.5 rounded-full bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-white disabled:opacity-50"
            >
              {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              Run analytics
            </button>
          </div>

          <div className="mt-3 h-[min(58vh,500px)]">
            <AnomalyPipelineMap
              phase={phase}
              bandOpacity={bandOpacity}
              bandFilter={canFilterBands ? bandFilter : null}
              highlightedParcelIndex={highlightedParcelIndex}
              className="h-full"
            />
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {(["green", "amber", "red"] as const).map((band) => {
              const active = bandFilter === band;
              return (
                <button
                  key={band}
                  type="button"
                  disabled={!canFilterBands}
                  onClick={() => toggleBandFilter(band)}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition disabled:opacity-40 ${
                    active
                      ? "border-slate-800 bg-slate-900 text-white"
                      : "border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: VARIANCE_BAND_COLORS[band].stroke }}
                  />
                  {VARIANCE_BAND_COLORS[band].label} · {VARIANCE_BAND_COLORS[band].threshold}
                </button>
              );
            })}
          </div>
        </section>

        <div key={runId} className="space-y-3">
          <AnimatePresence initial={false}>
            {(phase === "idle" || phase === "satellite") && !running ? (
              <motion.div
                key="intro"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="rounded-2xl border border-dashed border-slate-200 bg-white p-4"
              >
                <div className="flex items-center gap-2">
                  <Radar className="h-4 w-4 text-sky-600" />
                  <p className="text-sm font-semibold text-[#1A1A1A]">Scheduled analytics run</p>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  Celery job scopes parcels, compares geometry against RoR extent, overlays digitized vectors on
                  satellite imagery, and writes variance bands to the anomaly table for dashboard review.
                </p>
              </motion.div>
            ) : null}
          </AnimatePresence>

          <AnimatePresence initial={false}>
            {step >= 3 && checks.some((status) => status !== "pending") ? (
              <motion.section
                key="record-checks"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <p className="text-sm font-semibold text-[#1A1A1A]">Run record-map checks</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  Click flagged issues to zoom and cycle through affected parcels.
                </p>
                <ul className="mt-3 space-y-2">
                  {RECORD_MAP_CHECKS.map((check, index) => {
                    const status = checks[index];
                    const isFlagged = status === "flagged";
                    const isFocused = checkFocus?.checkId === check.id;
                    return (
                      <motion.li
                        key={check.id}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <button
                          type="button"
                          disabled={!isFlagged}
                          onClick={() => focusCheckParcel(check.id)}
                          className={`w-full rounded-xl border px-3 py-2 text-left text-xs transition ${
                            isFlagged
                              ? isFocused
                                ? "border-amber-400 bg-amber-100 text-amber-950 ring-2 ring-amber-300"
                                : "border-amber-200 bg-amber-50 text-amber-900 hover:border-amber-300"
                              : status === "done"
                                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                                : status === "running"
                                  ? "border-sky-200 bg-sky-50 text-sky-800"
                                  : "border-slate-200 bg-slate-50 text-slate-500"
                          } ${isFlagged ? "cursor-pointer" : "cursor-default"}`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-semibold">{check.label}</span>
                            {status === "running" ? (
                              <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
                            ) : status === "done" || status === "flagged" ? (
                              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                            ) : null}
                          </div>
                          {(status === "done" || status === "flagged") && (
                            <p className="mt-1 text-[11px] opacity-90">{check.detail}</p>
                          )}
                          {isFlagged && isFocused ? (
                            <p className="mt-1 text-[10px] font-medium text-amber-800">
                              Viewing parcel {(checkFocus?.cycleIndex ?? 0) + 1} of{" "}
                              {check.flaggedParcelIndices.length} — click again for next
                            </p>
                          ) : null}
                        </button>
                      </motion.li>
                    );
                  })}
                </ul>
              </motion.section>
            ) : null}
          </AnimatePresence>

          <AnimatePresence initial={false}>
            {analysisComplete ? (
              <motion.section
                key="export"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <button
                  type="button"
                  onClick={handleExport}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-sky-600 px-4 py-2.5 text-xs font-medium text-white hover:bg-sky-700"
                >
                  <Download className="h-3.5 w-3.5" />
                  Export anomaly list PDF/Excel + variance heat-map
                </button>
                {exportMessage ? (
                  <p className="mt-2 rounded-lg border border-sky-100 bg-sky-50 px-3 py-2 text-[11px] text-sky-800">
                    {exportMessage}
                  </p>
                ) : null}
              </motion.section>
            ) : null}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
