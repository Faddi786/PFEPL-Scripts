import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef } from "react";
import { createMapEngine } from "../../lib/mapEngine";
import { getRegionDataset } from "../../data/mockData";

export type NilAiMapHandle = {
  highlightParcels: (ids: string[]) => void;
  clearHighlights: () => void;
};

const NilAiMap = forwardRef<NilAiMapHandle>(function NilAiMap(_, ref) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const engineRef = useRef<ReturnType<typeof createMapEngine> | null>(null);
  const regionDataset = useMemo(() => getRegionDataset("puducherry"), []);

  useImperativeHandle(ref, () => ({
    highlightParcels: (ids) => engineRef.current?.highlightParcels(ids),
    clearHighlights: () => engineRef.current?.clearHighlights(),
  }));

  useEffect(() => {
    if (!mapRef.current || engineRef.current) return;

    engineRef.current = createMapEngine(mapRef.current, regionDataset, {});

    engineRef.current.setBasemap("basemap-carto");
    engineRef.current.setLayerVisibility("parcels", true);
    engineRef.current.setLayerVisibility("fmb", true);
    engineRef.current.setLayerVisibility("village", true);
    engineRef.current.setLayerVisibility("ward", false);
    engineRef.current.setLayerVisibility("variance", false);
    engineRef.current.setLayerVisibility("region", false);
    engineRef.current.setLayerVisibility("taluk", false);
    engineRef.current.setLayerVisibility("dgps", false);
    engineRef.current.setLayerVisibility("collabland", false);
    engineRef.current.setLayerVisibility("ortho", false);

    const map = engineRef.current.map;
    const resize = () => map.updateSize();
    requestAnimationFrame(resize);
    window.addEventListener("resize", resize);

    const observer = new ResizeObserver(resize);
    observer.observe(mapRef.current);

    return () => {
      window.removeEventListener("resize", resize);
      observer.disconnect();
      engineRef.current?.dispose();
      engineRef.current = null;
    };
  }, [regionDataset]);

  return (
    <div className="relative h-full min-h-0 overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
      <div ref={mapRef} className="h-full w-full" />
    </div>
  );
});

export default NilAiMap;
