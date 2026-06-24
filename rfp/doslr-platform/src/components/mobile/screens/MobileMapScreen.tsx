import { useEffect, useState } from "react";
import { Crosshair, Layers } from "lucide-react";
import type { MobileBasemapId } from "../MobileMapView";
import MobileMapView from "../MobileMapView";
import { useMobileApp } from "../MobileAppContext";

const basemapOptions: Array<{ id: MobileBasemapId; label: string }> = [
  { id: "basemap-carto", label: "Carto Positron" },
  { id: "basemap-osm", label: "OpenStreetMap" },
  { id: "basemap-imagery", label: "World Imagery" },
];

export default function MobileMapScreen() {
  const { openParcel, gnssPoints } = useMobileApp();
  const [layersOpen, setLayersOpen] = useState(false);
  const [dgpsOpen, setDgpsOpen] = useState(false);
  const [basemapId, setBasemapId] = useState<MobileBasemapId>("basemap-carto");
  const [showParcels, setShowParcels] = useState(true);
  const [dgpsShowPending, setDgpsShowPending] = useState(true);
  const [dgpsShowUploaded, setDgpsShowUploaded] = useState(true);
  const showDgps = dgpsShowPending || dgpsShowUploaded;

  useEffect(() => {
    if (!layersOpen && !dgpsOpen) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setLayersOpen(false);
        setDgpsOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [layersOpen, dgpsOpen]);

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white/90 px-3 py-2">
        <div>
          <p className="text-sm font-semibold text-[#1A1A1A]">Cadastral map</p>
          <p className="text-[10px] text-slate-500">Kurumbapet</p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              setDgpsOpen((v) => !v);
              setLayersOpen(false);
            }}
            className={`flex items-center gap-1 rounded-lg border px-2 py-1 text-[10px] font-medium transition ${
              showDgps ? "border-amber-300 bg-amber-50 text-amber-900" : "border-slate-200 bg-white text-slate-600"
            }`}
            title="Filter DGPS points"
          >
            <Crosshair className="h-3 w-3" />
            DGPS
          </button>
          <button
            type="button"
            onClick={() => {
              setLayersOpen((v) => !v);
              setDgpsOpen(false);
            }}
            className="flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-medium text-slate-600"
          >
            <Layers className="h-3 w-3" />
            Layers
          </button>
        </div>
      </div>

      {dgpsOpen ? (
        <>
          <button
            type="button"
            aria-label="Close DGPS filter"
            className="absolute inset-0 z-10 bg-black/5"
            onClick={() => setDgpsOpen(false)}
          />
          <div className="absolute right-[4.5rem] top-14 z-20 w-44 rounded-xl border border-slate-200 bg-white p-2.5 shadow-lg">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">DGPS filter</p>
            <label className="flex items-center gap-2 rounded-lg px-1.5 py-1 text-[11px] text-slate-700 hover:bg-slate-50">
              <input
                type="checkbox"
                checked={dgpsShowPending}
                onChange={() => setDgpsShowPending((v) => !v)}
              />
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                Upload pending
              </span>
            </label>
            <label className="flex items-center gap-2 rounded-lg px-1.5 py-1 text-[11px] text-slate-700 hover:bg-slate-50">
              <input
                type="checkbox"
                checked={dgpsShowUploaded}
                onChange={() => setDgpsShowUploaded((v) => !v)}
              />
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Uploaded
              </span>
            </label>
          </div>
        </>
      ) : null}

      {layersOpen ? (
        <>
          <button
            type="button"
            aria-label="Close layers"
            className="absolute inset-0 z-10 bg-black/5"
            onClick={() => setLayersOpen(false)}
          />
          <div className="absolute right-3 top-14 z-20 w-44 rounded-xl border border-slate-200 bg-white p-2.5 shadow-lg">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Basemap</p>
            <div className="space-y-1">
              {basemapOptions.map((opt) => (
                <label
                  key={opt.id}
                  className="flex cursor-pointer items-center gap-2 rounded-lg px-1.5 py-1 text-[11px] text-slate-700 hover:bg-slate-50"
                >
                  <input
                    type="radio"
                    name="mobile-basemap"
                    checked={basemapId === opt.id}
                    onChange={() => setBasemapId(opt.id)}
                  />
                  {opt.label}
                </label>
              ))}
            </div>
            <p className="mb-1.5 mt-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Overlays</p>
            <label className="flex items-center gap-2 text-[11px] text-slate-700">
              <input type="checkbox" checked={showParcels} onChange={() => setShowParcels((v) => !v)} />
              Parcels
            </label>
          </div>
        </>
      ) : null}

      <div className="relative min-h-0 flex-1 overflow-hidden">
        <MobileMapView
          basemapId={basemapId}
          showParcels={showParcels}
          showDgps={showDgps}
          dgpsShowPending={dgpsShowPending}
          dgpsShowUploaded={dgpsShowUploaded}
          gnssPoints={gnssPoints}
          onParcelClick={openParcel}
        />
      </div>
    </div>
  );
}
