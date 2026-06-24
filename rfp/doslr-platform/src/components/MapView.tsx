import { useEffect, useMemo, useRef, useState } from "react";
import { Sparkles } from "lucide-react";
import MapToolsDropdown from "./MapToolsDropdown";
import { createMapEngine, type MapTool } from "../lib/mapEngine";
import {
  getRegionDataset,
  PARCEL_DISPLAY_FIELDS,
  type LayerGroup,
  type ParcelRecord,
  type RegionKey,
} from "../data/mockData";

type Props = {
  regionKey: RegionKey;
  layerGroups: LayerGroup[];
  basemapId: string;
};

function formatParcelValue(key: keyof ParcelRecord, value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  if (key === "areaSqM") return Number(value).toLocaleString();
  if (key === "variancePct") return `${Number(value).toFixed(2)}%`;
  if (key === "plotFrontageM" || key === "plotDepthM") return `${value} m`;
  return String(value);
}

export default function MapView({ regionKey, layerGroups, basemapId }: Props) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const engineRef = useRef<ReturnType<typeof createMapEngine> | null>(null);
  const [activeTool, setActiveTool] = useState<MapTool>("none");
  const [toast, setToast] = useState<string | null>(null);
  const [parcelContext, setParcelContext] = useState<ParcelRecord | null>(null);

  const regionDataset = useMemo(() => getRegionDataset(regionKey), [regionKey]);

  useEffect(() => {
    if (!mapRef.current || engineRef.current) return;
    engineRef.current = createMapEngine(mapRef.current, regionDataset, {
      onToast: (message) => setToast(message),
      onParcelContext: (parcel) => setParcelContext(parcel as ParcelRecord),
    });

    const map = engineRef.current.map;
    const resize = () => map.updateSize();
    requestAnimationFrame(resize);
    window.addEventListener("resize", resize);

    const observer = new ResizeObserver(resize);
    if (mapRef.current) observer.observe(mapRef.current);

    return () => {
      window.removeEventListener("resize", resize);
      observer.disconnect();
      engineRef.current?.dispose();
      engineRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    engineRef.current?.setDataset(regionDataset);
  }, [regionDataset]);

  useEffect(() => {
    engineRef.current?.setBasemap(basemapId);
  }, [basemapId]);

  useEffect(() => {
    layerGroups.forEach((group) => {
      group.layers.forEach((layer) => engineRef.current?.setLayerVisibility(layer.id, layer.visible));
    });
  }, [layerGroups]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      setParcelContext(null);
      setToast(null);
      setActiveTool("none");
      engineRef.current?.resetTools(true);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function handleSelectTool(tool: MapTool) {
    setActiveTool(tool);
    engineRef.current?.setTool(tool);
  }

  return (
    <div className="relative h-full min-h-0 overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
      <div ref={mapRef} className="absolute inset-0" />

      {toast ? (
        <div className="pointer-events-none absolute left-4 top-4 flex flex-col gap-2">
          <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-white/80 bg-white/90 px-3 py-2 shadow-sm backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5 text-sky-600" />
            <span className="text-xs font-medium text-slate-700">{toast}</span>
          </div>
        </div>
      ) : null}

      <MapToolsDropdown activeTool={activeTool} onSelectTool={handleSelectTool} />

      {parcelContext ? (
        <div className="absolute bottom-4 left-4 max-h-[62vh] w-[min(320px,calc(100%-2rem))] overflow-hidden rounded-2xl border border-white/80 bg-white/95 shadow-lg backdrop-blur-sm">
          <div className="border-b border-slate-100 px-3 py-2.5">
            <p className="text-xs font-semibold text-[#1A1A1A]">Parcel Context</p>
            <p className="mt-0.5 text-[11px] text-slate-500">
              {parcelContext.id} • {parcelContext.region}
            </p>
          </div>
          <div className="max-h-[52vh] overflow-y-auto px-3 py-2">
            <dl className="space-y-1.5">
              {PARCEL_DISPLAY_FIELDS.map(({ key, label }) => (
                <div key={key} className="grid grid-cols-[112px_1fr] gap-2 text-[11px] leading-4">
                  <dt className="text-slate-500">{label}</dt>
                  <dd className="font-medium text-slate-800">{formatParcelValue(key, parcelContext[key])}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      ) : null}
    </div>
  );
}
