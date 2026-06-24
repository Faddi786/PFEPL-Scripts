import { useEffect, useMemo, useRef } from "react";
import Map from "ol/Map";
import View from "ol/View";
import { defaults as defaultControls } from "ol/control";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import { getCenter } from "ol/extent";
import { Fill, Stroke, Style, Text } from "ol/style";
import type Feature from "ol/Feature";
import type { Geometry } from "ol/geom";
import {
  type AnomalyPipelinePhase,
  type VarianceBand,
  VARIANCE_BAND_COLORS,
  offsetPolygon,
  pickDemoParcels,
} from "./anomalyPipelineData";

const MAP_MAX_ZOOM = 19;

function phaseBadgeClass(phase: AnomalyPipelinePhase, bandFilter: VarianceBand | null) {
  if (bandFilter) {
    const byBand = {
      green: "bg-emerald-600 ring-emerald-300",
      amber: "bg-amber-500 ring-amber-200",
      red: "bg-red-600 ring-red-300",
    };
    return byBand[bandFilter];
  }
  switch (phase) {
    case "idle":
    case "satellite":
      return "bg-sky-600 ring-sky-300";
    case "digitized":
      return "bg-blue-600 ring-blue-300";
    case "comparing":
      return "bg-cyan-600 ring-cyan-300";
    case "bands":
      return "bg-amber-500 ring-amber-200";
    case "boundary":
      return "bg-orange-500 ring-orange-200";
    case "complete":
      return "bg-emerald-600 ring-emerald-300";
    default:
      return "bg-slate-600 ring-slate-300";
  }
}

function phaseBadgeLabel(phase: AnomalyPipelinePhase, bandFilter: VarianceBand | null) {
  if (bandFilter) return `Filtered: ${VARIANCE_BAND_COLORS[bandFilter].label}`;
  if (phase === "idle" || phase === "satellite") return "Satellite imagery";
  if (phase === "digitized") return "Digitized cadastral layer";
  if (phase === "comparing") return "Comparing ST_Area vs RoR extent";
  if (phase === "bands") return "Variance bands applying…";
  if (phase === "boundary") return "Boundary deviation flags";
  return "Analysis complete";
}

type Props = {
  phase: AnomalyPipelinePhase;
  bandOpacity: number;
  bandFilter?: VarianceBand | null;
  highlightedParcelIndex?: number | null;
  className?: string;
};

export default function AnomalyPipelineMap({
  phase,
  bandOpacity,
  bandFilter = null,
  highlightedParcelIndex = null,
  className,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const phaseRef = useRef(phase);
  const bandOpacityRef = useRef(bandOpacity);
  const bandFilterRef = useRef(bandFilter);
  const highlightedRef = useRef(highlightedParcelIndex);
  const digitizedLayerRef = useRef<VectorLayer<VectorSource> | null>(null);
  const varianceLayerRef = useRef<VectorLayer<VectorSource> | null>(null);
  const varianceSourceRef = useRef<VectorSource | null>(null);
  const contextLayerRef = useRef<VectorLayer<VectorSource> | null>(null);

  const demoParcels = useMemo(() => pickDemoParcels(), []);

  phaseRef.current = phase;
  bandOpacityRef.current = bandOpacity;
  bandFilterRef.current = bandFilter;
  highlightedRef.current = highlightedParcelIndex;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const format = new GeoJSON();

    const imagery = new TileLayer({
      source: new XYZ({
        url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attributions: "Tiles © Esri",
        maxZoom: 19,
        crossOrigin: "anonymous",
      }),
    });

    const contextSource = new VectorSource({
      features: format.readFeatures(
        { type: "FeatureCollection", features: demoParcels },
        { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" },
      ),
    });
    contextSource.getFeatures().forEach((feature, index) => {
      (feature as Feature<Geometry>).set("parcelIndex", index);
      (feature as Feature<Geometry>).set("varianceBand", demoParcels[index].properties?.varianceBand);
    });

    const contextLayer = new VectorLayer({
      source: contextSource,
      zIndex: 2,
      style: (feature) => {
        const filter = bandFilterRef.current;
        const band = String(feature.get("varianceBand") ?? "green") as VarianceBand;
        if (filter && band !== filter) return undefined;
        return new Style({
          stroke: new Stroke({ color: "rgba(255,255,255,0.45)", width: 1.2 }),
          fill: new Fill({ color: "rgba(255,255,255,0.06)" }),
        });
      },
    });
    contextLayerRef.current = contextLayer;

    const digitizedFeatures = demoParcels.map((parcel) => {
      const feature = format.readFeature(offsetPolygon(parcel, Number(parcel.properties?.demoDigitizedOffset ?? 0)), {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }) as Feature<Geometry>;
      return feature;
    });
    digitizedFeatures.forEach((feature, index) => {
      feature.set("parcelIndex", index);
      feature.set("varianceBand", demoParcels[index].properties?.varianceBand);
      feature.set("surveyNo", String(demoParcels[index].properties?.surveyNo ?? ""));
    });

    const digitizedSource = new VectorSource({ features: digitizedFeatures });
    const digitizedLayer = new VectorLayer({
      source: digitizedSource,
      zIndex: 4,
      visible: false,
      style: (feature, resolution) => {
        const currentPhase = phaseRef.current;
        const show =
          currentPhase === "digitized" ||
          currentPhase === "comparing" ||
          (currentPhase === "boundary" && bandOpacityRef.current < 0.85);
        if (!show) return undefined;

        const filter = bandFilterRef.current;
        const band = String(feature.get("varianceBand") ?? "green") as VarianceBand;
        if (filter && band !== filter) return undefined;

        const surveyNo = String(feature.get("surveyNo") ?? "");
        const parcelIndex = feature.get("parcelIndex") as number;
        const highlighted = highlightedRef.current === parcelIndex;

        return new Style({
          stroke: new Stroke({
            color: highlighted ? "#ffffff" : currentPhase === "comparing" ? "#38bdf8" : "#2563eb",
            width: highlighted ? 3.2 : currentPhase === "comparing" ? 2.2 : 1.8,
            lineDash: currentPhase === "comparing" ? [8, 5] : undefined,
          }),
          fill: new Fill({ color: highlighted ? "rgba(255,255,255,0.28)" : "rgba(37,99,235,0.22)" }),
          text:
            surveyNo && resolution < 8
              ? new Text({
                  text: surveyNo,
                  font: "600 9px ui-monospace,Consolas,monospace",
                  fill: new Fill({ color: "#eff6ff" }),
                  stroke: new Stroke({ color: "#1e3a8a", width: 2 }),
                })
              : undefined,
        });
      },
    });
    digitizedLayerRef.current = digitizedLayer;

    const varianceSource = new VectorSource({
      features: format.readFeatures(
        { type: "FeatureCollection", features: demoParcels },
        { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" },
      ),
    });
    varianceSourceRef.current = varianceSource;
    varianceSource.getFeatures().forEach((feature, index) => {
      const typed = feature as Feature<Geometry>;
      typed.set("parcelIndex", index);
      typed.set("varianceBand", demoParcels[index].properties?.varianceBand);
      typed.set("surveyNo", String(demoParcels[index].properties?.surveyNo ?? ""));
      typed.set("boundaryFlag", Boolean(demoParcels[index].properties?.boundaryFlag));
    });

    const varianceLayer = new VectorLayer({
      source: varianceSource,
      zIndex: 5,
      visible: false,
      style: (feature, resolution) => {
        const currentPhase = phaseRef.current;
        const opacity = bandOpacityRef.current;
        const showBands =
          (currentPhase === "bands" || currentPhase === "boundary" || currentPhase === "complete") && opacity > 0;
        if (!showBands) return undefined;

        const band = String(feature.get("varianceBand") ?? "green") as VarianceBand;
        const filter = bandFilterRef.current;
        if (filter && band !== filter) return undefined;

        const colors = VARIANCE_BAND_COLORS[band] ?? VARIANCE_BAND_COLORS.green;
        const boundaryFlag = Boolean(feature.get("boundaryFlag"));
        const showBoundary = currentPhase === "boundary" || currentPhase === "complete";
        const parcelIndex = feature.get("parcelIndex") as number;
        const highlighted = highlightedRef.current === parcelIndex;

        const fillColor = colors.fill.replace(/[\d.]+\)$/, `${(highlighted ? 0.72 : 0.55) * opacity})`);
        const surveyNo = String(feature.get("surveyNo") ?? "");

        return new Style({
          fill: new Fill({ color: fillColor }),
          stroke: new Stroke({
            color: highlighted ? "#ffffff" : showBoundary && boundaryFlag ? "#f97316" : colors.stroke,
            width: highlighted ? 3.4 : showBoundary && boundaryFlag ? 2.4 : 1.8,
            lineDash: !highlighted && showBoundary && boundaryFlag ? [8, 5] : undefined,
          }),
          text:
            surveyNo && resolution < 8 && opacity > 0.35
              ? new Text({
                  text: surveyNo,
                  font: "600 9px ui-monospace,Consolas,monospace",
                  fill: new Fill({ color: "#111" }),
                  stroke: new Stroke({ color: "#fff", width: 2 }),
                })
              : undefined,
        });
      },
    });
    varianceLayerRef.current = varianceLayer;

    const map = new Map({
      target: containerRef.current,
      controls: defaultControls({ zoom: false, attribution: false }),
      layers: [imagery, contextLayer, digitizedLayer, varianceLayer],
      view: new View({ zoom: 17, maxZoom: MAP_MAX_ZOOM, minZoom: 14 }),
    });

    const extent = contextSource.getExtent();
    if (extent) {
      map.getView().fit(extent, { padding: [14, 14, 14, 14], duration: 0, maxZoom: MAP_MAX_ZOOM });
      const zoom = map.getView().getZoom();
      if (zoom !== undefined) {
        map.getView().setZoom(Math.min(MAP_MAX_ZOOM, zoom * 1.05));
      }
    }

    mapRef.current = map;

    const resize = () => map.updateSize();
    requestAnimationFrame(resize);
    const observer = new ResizeObserver(resize);
    observer.observe(containerRef.current);
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      observer.disconnect();
      map.setTarget(undefined);
      mapRef.current = null;
      digitizedLayerRef.current = null;
      varianceLayerRef.current = null;
      varianceSourceRef.current = null;
      contextLayerRef.current = null;
    };
  }, [demoParcels]);

  useEffect(() => {
    const digitizedLayer = digitizedLayerRef.current;
    const varianceLayer = varianceLayerRef.current;
    const contextLayer = contextLayerRef.current;
    if (!digitizedLayer || !varianceLayer) return;

    const showDigitized =
      phase === "digitized" || phase === "comparing" || (phase === "boundary" && bandOpacity < 0.85);
    const showVariance =
      (phase === "bands" || phase === "boundary" || phase === "complete") && bandOpacity > 0;

    digitizedLayer.setVisible(showDigitized);
    varianceLayer.setVisible(showVariance);
    digitizedLayer.changed();
    varianceLayer.changed();
    contextLayer?.changed();
  }, [phase, bandOpacity, bandFilter, highlightedParcelIndex]);

  useEffect(() => {
    const map = mapRef.current;
    const source = varianceSourceRef.current;
    if (!map || !source || highlightedParcelIndex == null) return;

    const feature = source.getFeatures()[highlightedParcelIndex] as Feature<Geometry> | undefined;
    const geometry = feature?.getGeometry();
    if (!geometry) return;

    const extent = geometry.getExtent();
    const center = getCenter(extent);
    map.getView().animate({ center, zoom: MAP_MAX_ZOOM, duration: 450 });
  }, [highlightedParcelIndex]);

  const badgeActive = phase !== "idle" && phase !== "complete" && !bandFilter;

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-slate-200 bg-slate-900 ${className ?? ""}`}
    >
      <div ref={containerRef} className="h-full w-full min-h-[360px]" />
      <div
        className={`pointer-events-none absolute left-2 top-2 rounded-full px-2.5 py-1 text-[10px] font-semibold text-white shadow-md ring-2 ${phaseBadgeClass(phase, bandFilter)} ${badgeActive ? "animate-pulse" : ""}`}
      >
        {phaseBadgeLabel(phase, bandFilter)}
      </div>
    </div>
  );
}
