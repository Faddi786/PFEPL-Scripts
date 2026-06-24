import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Smartphone } from "lucide-react";
import { Link } from "react-router-dom";
import MobileApp from "../components/mobile/MobileApp";

type View = "lobby" | "theatre";

/** Chrome/Edge auto-hide the native “Press Esc to exit” hint after ~3s — reveal phone after that. */
const FULLSCREEN_HINT_DELAY_MS = 3200;

async function enterFullscreen(element: HTMLElement) {
  const request = element.requestFullscreen?.bind(element);
  if (!request) return;

  try {
    await request({ navigationUI: "hide" } as FullscreenOptions);
  } catch {
    await request();
  }
}

async function leaveFullscreen() {
  if (document.fullscreenElement) {
    try {
      await document.exitFullscreen();
    } catch {
      /* ignore */
    }
  }
}

export default function NilamMobilePage() {
  const [view, setView] = useState<View>("lobby");
  const [showPhone, setShowPhone] = useState(false);
  const revealTimers = useRef<number[]>([]);
  const theatreRef = useRef<HTMLDivElement>(null);

  const clearRevealTimers = useCallback(() => {
    revealTimers.current.forEach((id) => window.clearTimeout(id));
    revealTimers.current = [];
  }, []);

  const exitTheatre = useCallback(() => {
    clearRevealTimers();
    setShowPhone(false);
    setView("lobby");
    void leaveFullscreen();
  }, [clearRevealTimers]);

  const beginPresentation = useCallback(() => {
    clearRevealTimers();
    setShowPhone(false);
    setView("theatre");
  }, [clearRevealTimers]);

  useEffect(() => {
    if (view !== "theatre") return;

    const theatre = theatreRef.current;
    if (!theatre) return;

    void enterFullscreen(theatre);

    const timer = window.setTimeout(() => setShowPhone(true), FULLSCREEN_HINT_DELAY_MS);
    revealTimers.current.push(timer);

    return () => {
      clearRevealTimers();
    };
  }, [view, clearRevealTimers]);

  useEffect(() => {
    function onFullscreenChange() {
      if (!document.fullscreenElement && view === "theatre") {
        clearRevealTimers();
        setShowPhone(false);
        setView("lobby");
      }
    }
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, [view, clearRevealTimers]);

  useEffect(() => {
    if (view !== "theatre") return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") exitTheatre();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [view, exitTheatre]);

  return (
    <>
      {view === "theatre" ? (
        <div
          ref={theatreRef}
          className="fixed inset-0 z-[200] flex items-center justify-center bg-black"
        >
          {showPhone ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 3, ease: "easeInOut" }}
            >
              <MobileApp theatre />
            </motion.div>
          ) : null}
        </div>
      ) : null}

      <div className="flex h-screen flex-col overflow-hidden bg-[#F7F7F5] p-3 lg:p-4">
        <main className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-white/70 bg-white/85 px-4 py-3 shadow-[0_8px_30px_rgba(0,0,0,0.06)] lg:px-5">
          <div className="relative flex shrink-0 items-center py-2">
            <Link
              to="/app"
              className="relative z-10 inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 transition hover:text-slate-800"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to map
            </Link>
            <div className="pointer-events-none absolute inset-x-0 flex items-center justify-center">
              <div className="flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-slate-700" />
                <h2 className="text-base font-semibold text-[#1A1A1A]">Nilam Mobile</h2>
              </div>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col">
            <div className="h-[1.5%] shrink-0" aria-hidden />
            <button
              type="button"
              onClick={beginPresentation}
              className="group relative min-h-0 flex-1 overflow-hidden rounded-[2rem] bg-black transition hover:bg-[#0a0a0a]"
            >
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_38%,rgba(255,255,255,0.08),transparent_52%)]" />
              <div className="flex h-full items-center justify-center">
                <p className="text-[clamp(1.35rem,2.4vw,2rem)] font-light tracking-[-0.02em] text-white/90 transition group-hover:text-white">
                  Click to begin
                </p>
              </div>
            </button>
          </div>
        </main>
      </div>
    </>
  );
}
