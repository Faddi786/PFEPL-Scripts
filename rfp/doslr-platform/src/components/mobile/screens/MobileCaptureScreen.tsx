import { AnimatePresence, motion } from "framer-motion";
import { Bluetooth, Crosshair, Radio, Unplug } from "lucide-react";
import { useMobileApp } from "../MobileAppContext";

const cardTransition = { duration: 0.38, ease: [0.4, 0, 0.2, 1] as const };

export default function MobileCaptureScreen() {
  const { gnssConnected, gnssPoints, connectGnss, disconnectGnss, captureGnssPoint } = useMobileApp();

  const liveLat = 11.93752;
  const liveLng = 79.80841;
  const liveAcc = gnssConnected ? 0.09 : null;

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-slate-200 bg-white px-4 py-3">
        <p className="text-sm font-semibold text-[#1A1A1A]">DGPS / GNSS capture</p>
        <p className="text-[10px] text-slate-500">Bluetooth · NTRIP · file import</p>
      </div>

      <div className="p-4">
        <motion.div
          layout
          transition={cardTransition}
          className={`mb-4 overflow-hidden rounded-2xl border p-4 transition-colors duration-300 ${
            gnssConnected ? "border-emerald-200 bg-emerald-50/60" : "border-slate-200 bg-white"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio
                className={`h-5 w-5 transition-colors duration-300 ${
                  gnssConnected ? "text-emerald-600" : "text-slate-400"
                }`}
              />
              <div>
                <p className="text-sm font-semibold text-[#1A1A1A]">
                  {gnssConnected ? "Rover connected" : "No rover connected"}
                </p>
                <p className="text-[10px] text-slate-500">
                  {gnssConnected ? "Trimble R12 · Bluetooth" : "Connect DGPS rover to begin"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={gnssConnected ? disconnectGnss : connectGnss}
              className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors duration-300 ${
                gnssConnected ? "bg-white text-slate-700" : "bg-[#1A1A1A] text-white"
              }`}
            >
              {gnssConnected ? (
                <>
                  <Unplug className="h-3 w-3" /> Disconnect
                </>
              ) : (
                <>
                  <Bluetooth className="h-3 w-3" /> Connect
                </>
              )}
            </button>
          </div>

          <AnimatePresence initial={false}>
            {gnssConnected ? (
              <motion.div
                key="rover-metrics"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={cardTransition}
                className="overflow-hidden"
              >
                <motion.div
                  initial={{ y: -6 }}
                  animate={{ y: 0 }}
                  exit={{ y: -6 }}
                  transition={cardTransition}
                  className="mt-3 grid grid-cols-3 gap-2 text-center"
                >
                  <div className="rounded-lg bg-white/80 p-2">
                    <p className="text-[10px] text-slate-500">Lat</p>
                    <p className="text-xs font-mono font-semibold">{liveLat.toFixed(5)}</p>
                  </div>
                  <div className="rounded-lg bg-white/80 p-2">
                    <p className="text-[10px] text-slate-500">Lng</p>
                    <p className="text-xs font-mono font-semibold">{liveLng.toFixed(5)}</p>
                  </div>
                  <div className="rounded-lg bg-white/80 p-2">
                    <p className="text-[10px] text-slate-500">Accuracy</p>
                    <p className="text-xs font-semibold">{liveAcc} m</p>
                  </div>
                </motion.div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.div>

        <button
          type="button"
          disabled={!gnssConnected}
          onClick={captureGnssPoint}
          className="mb-4 flex w-full items-center justify-center gap-2 rounded-full bg-[#1A1A1A] py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <Crosshair className="h-4 w-4" />
          Capture control point
        </button>

        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Captured points ({gnssPoints.length})
        </p>
        <div className="space-y-2">
          {gnssPoints.map((point) => (
            <div key={point.id} className="rounded-xl border border-slate-200 bg-white p-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-[#1A1A1A]">{point.label}</p>
                  <p className="text-[10px] text-slate-500">{point.capturedAt}</p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    point.synced ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {point.synced ? "Synced" : "Pending"}
                </span>
              </div>
              <p className="mt-1 font-mono text-[11px] text-slate-600">
                {point.lat.toFixed(5)}, {point.lng.toFixed(5)} · ±{point.accuracyM}m · {point.source}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
