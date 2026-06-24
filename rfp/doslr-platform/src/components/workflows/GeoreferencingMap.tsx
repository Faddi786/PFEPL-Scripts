import { useEffect, useRef } from "react";
import Map from "ol/Map";
import View from "ol/View";
import { defaults as defaultControls } from "ol/control";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import Modify from "ol/interaction/Modify";
import { fromLonLat } from "ol/proj";
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from "ol/style";
import type Feature from "ol/Feature";
import type { Geometry } from "ol/geom";
import { getRegionDataset } from "../../data/mockData";

type Props = {
  showDgps: boolean;
  editable?: boolean;
  className?: string;
  onPointsMoved?: () => void;
};

function dgpsStyle(feature: Feature<Geometry>) {
  const id = String(feature.get("id") ?? "").replace(/^PY-/, "");
  return new Style({
    image: new CircleStyle({
      radius: 7,
      fill: new Fill({ color: "#f59e0b" }),
      stroke: new Stroke({ color: "#ffffff", width: 2.5 }),
    }),
    text: new Text({
      text: id.replace("GCP-", ""),
      font: "600 9px Inter, sans-serif",
      fill: new Fill({ color: "#92400e" }),
      stroke: new Stroke({ color: "#ffffff", width: 2 }),
      offsetY: -14,
    }),
  });
}

export default function GeoreferencingMap({ showDgps, editable = false, className, onPointsMoved }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const dgpsSourceRef = useRef<VectorSource | null>(null);
  const onPointsMovedRef = useRef(onPointsMoved);
  const dgpsLoadedRef = useRef(false);

  onPointsMovedRef.current = onPointsMoved;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const dataset = getRegionDataset("puducherry");
    const format = new GeoJSON();

    const basemap = new TileLayer({
      source: new XYZ({
        url: "https://{a-d}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        attributions: "&copy; OpenStreetMap contributors &copy; CARTO",
      }),
    });

    const parcelSource = new VectorSource({
      features: format.readFeatures(dataset.geojson.parcels, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }),
    });

    const parcelLayer = new VectorLayer({
      source: parcelSource,
      zIndex: 1,
      style: new Style({
        stroke: new Stroke({ color: "#94a3b8", width: 1 }),
        fill: new Fill({ color: "rgba(148,163,184,0.2)" }),
      }),
    });

    const dgpsSource = new VectorSource();
    dgpsSourceRef.current = dgpsSource;

    const dgpsLayer = new VectorLayer({
      source: dgpsSource,
      zIndex: 3,
      style: (feature) => dgpsStyle(feature as Feature<Geometry>),
    });

    const map = new Map({
      target: containerRef.current,
      controls: defaultControls({ zoom: true, attribution: false }),
      layers: [basemap, parcelLayer, dgpsLayer],
      view: new View({
        center: fromLonLat(dataset.cadastralView.center),
        zoom: dataset.cadastralView.zoom,
      }),
    });

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
      dgpsSourceRef.current = null;
      dgpsLoadedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const source = dgpsSourceRef.current;
    if (!source || !showDgps || dgpsLoadedRef.current) return;

    const dataset = getRegionDataset("puducherry");
    const format = new GeoJSON();
    const features = format.readFeatures(dataset.geojson.dgps, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    });
    source.addFeatures(features);
    dgpsLoadedRef.current = true;

    const map = mapRef.current;
    if (map) {
      const extent = source.getExtent();
      if (extent) {
        map.getView().fit(extent, { padding: [48, 48, 48, 48], duration: 350, maxZoom: 18 });
      }
    }
  }, [showDgps]);

  useEffect(() => {
    const map = mapRef.current;
    const source = dgpsSourceRef.current;
    if (!map || !source) return;

    const existing = map
      .getInteractions()
      .getArray()
      .filter((interaction) => interaction instanceof Modify);
    existing.forEach((interaction) => map.removeInteraction(interaction));

    if (!editable || !showDgps) return;

    const modify = new Modify({ source });
    modify.on("modifyend", () => onPointsMovedRef.current?.());
    map.addInteraction(modify);

    return () => {
      map.removeInteraction(modify);
    };
  }, [editable, showDgps]);

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100 ${className ?? ""}`}
    >
      <div ref={containerRef} className="h-full w-full min-h-[320px]" />
    </div>
  );
}
