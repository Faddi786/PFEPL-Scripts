import { useEffect, useRef } from "react";
import Map from "ol/Map";
import View from "ol/View";
import { defaults as defaultControls } from "ol/control";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import OSM from "ol/source/OSM";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import { fromLonLat } from "ol/proj";
import { Fill, Stroke, Style, Circle as CircleStyle, Text } from "ol/style";
import type Feature from "ol/Feature";
import type { Geometry } from "ol/geom";
import { getRegionDataset } from "../../data/mockData";
import type { CapturedGnssPoint } from "../../data/mobileApp";

export type MobileBasemapId = "basemap-carto" | "basemap-osm" | "basemap-imagery";

type Props = {
  basemapId: MobileBasemapId;
  showParcels: boolean;
  showDgps: boolean;
  dgpsShowPending: boolean;
  dgpsShowUploaded: boolean;
  gnssPoints: CapturedGnssPoint[];
  onParcelClick: (parcelId: string) => void;
};

type ParcelGeoFeature = {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: number[][][] };
  properties?: Record<string, unknown>;
};

function gnssToFeatures(points: CapturedGnssPoint[]) {
  return {
    type: "FeatureCollection" as const,
    features: points.map((point) => ({
      type: "Feature" as const,
      properties: { id: point.id, label: point.label, synced: point.synced },
      geometry: { type: "Point" as const, coordinates: [point.lng, point.lat] },
    })),
  };
}

function pointOnRing(ring: number[][], t: number): [number, number] {
  const segments: Array<{ len: number; ax: number; ay: number; bx: number; by: number }> = [];
  let total = 0;

  for (let i = 0; i < ring.length - 1; i++) {
    const [ax, ay] = ring[i];
    const [bx, by] = ring[i + 1];
    const len = Math.hypot(bx - ax, by - ay);
    segments.push({ len, ax, ay, bx, by });
    total += len;
  }

  if (total === 0) return [ring[0][0], ring[0][1]];

  let dist = t * total;
  for (const seg of segments) {
    if (dist <= seg.len) {
      const f = seg.len > 0 ? dist / seg.len : 0;
      return [seg.ax + (seg.bx - seg.ax) * f, seg.ay + (seg.by - seg.ay) * f];
    }
    dist -= seg.len;
  }

  const [lng, lat] = ring[ring.length - 2];
  return [lng, lat];
}

function buildDgpsOnParcelsCollection(parcelFeatures: ParcelGeoFeature[]) {
  const polygons = parcelFeatures.filter((f) => f.geometry?.type === "Polygon" && f.geometry.coordinates[0]?.length);
  const count = 30;

  const points = Array.from({ length: count }).map((_, index) => {
    const parcel = polygons[index % polygons.length] ?? polygons[0];
    const ring = parcel.geometry.coordinates[0];
    const seed = (index + 1) * 7919;
    const t = 0.04 + (((seed * 9301 + 49297) % 233280) / 233280) * 0.92;
    const [lng, lat] = pointOnRing(ring, t);

    return {
      type: "Feature" as const,
      properties: {
        id: `PY-GCP-${String(index + 1).padStart(2, "0")}`,
        source: index % 3 === 0 ? "DGPS Rover" : index % 3 === 1 ? "GNSS RTK" : "NTRIP",
        rmse: Number((0.05 + (index % 5) * 0.04).toFixed(2)),
        uploaded: index % 3 !== 0,
      },
      geometry: { type: "Point" as const, coordinates: [lng, lat] },
    };
  });

  return {
    type: "FeatureCollection" as const,
    features: points,
  };
}

function dgpsPointStyle(feature: Feature<Geometry>, showPending: boolean, showUploaded: boolean) {
  const uploaded = Boolean(feature.get("uploaded"));
  if ((uploaded && !showUploaded) || (!uploaded && !showPending)) return undefined;

  const color = uploaded ? "#10b981" : "#f59e0b";

  return new Style({
    image: new CircleStyle({
      radius: 5,
      fill: new Fill({ color }),
      stroke: new Stroke({ color: "#ffffff", width: 2 }),
    }),
    text: new Text({
      text: String(feature.get("id") || "").replace("PY-GCP-", ""),
      font: "600 8px Inter, sans-serif",
      fill: new Fill({ color: uploaded ? "#065f46" : "#92400e" }),
      stroke: new Stroke({ color: "#ffffff", width: 2 }),
      offsetY: -12,
    }),
  });
}

export default function MobileMapView({
  basemapId,
  showParcels,
  showDgps,
  dgpsShowPending,
  dgpsShowUploaded,
  gnssPoints,
  onParcelClick,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const basemapLayersRef = useRef<Record<MobileBasemapId, TileLayer>>({} as Record<MobileBasemapId, TileLayer>);
  const parcelLayerRef = useRef<VectorLayer<VectorSource> | null>(null);
  const dgpsLayerRef = useRef<VectorLayer<VectorSource> | null>(null);
  const capturedLayerRef = useRef<VectorLayer<VectorSource> | null>(null);
  const onParcelClickRef = useRef(onParcelClick);
  const dgpsFilterRef = useRef({ pending: dgpsShowPending, uploaded: dgpsShowUploaded });

  onParcelClickRef.current = onParcelClick;
  dgpsFilterRef.current = { pending: dgpsShowPending, uploaded: dgpsShowUploaded };

  useEffect(() => {
    const target = containerRef.current;
    if (!target) return;

    const dataset = getRegionDataset("puducherry");
    const format = new GeoJSON();

    const basemapCarto = new TileLayer({
      source: new XYZ({
        url: "https://{a-d}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        attributions: "&copy; OpenStreetMap &copy; CARTO",
      }),
      visible: true,
    });
    const basemapOSM = new TileLayer({ source: new OSM(), visible: false });
    const basemapImagery = new TileLayer({
      source: new XYZ({
        url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      }),
      visible: false,
    });

    basemapLayersRef.current = {
      "basemap-carto": basemapCarto,
      "basemap-osm": basemapOSM,
      "basemap-imagery": basemapImagery,
    };

    const parcelSource = new VectorSource({
      features: format.readFeatures(dataset.geojson.parcels, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }),
    });

    const parcelLayer = new VectorLayer({
      source: parcelSource,
      zIndex: 9,
      style: (feature, resolution) => {
        const surveyNo = String(feature.get("surveyNo") || "");
        return new Style({
          stroke: new Stroke({ color: "#0f172a", width: 1.4 }),
          fill: new Fill({ color: "rgba(248, 113, 113, 0.35)" }),
          text:
            resolution < 6 && surveyNo
              ? new Text({
                  text: surveyNo,
                  font: "600 9px Inter, system-ui, sans-serif",
                  fill: new Fill({ color: "#111827" }),
                  stroke: new Stroke({ color: "#ffffff", width: 2.5 }),
                  overflow: true,
                })
              : undefined,
        });
      },
    });
    parcelLayerRef.current = parcelLayer;

    const dgpsCollection = buildDgpsOnParcelsCollection(
      dataset.geojson.parcels.features as ParcelGeoFeature[],
    );

    const dgpsSource = new VectorSource({
      features: format.readFeatures(dgpsCollection, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }),
    });

    const dgpsLayer = new VectorLayer({
      source: dgpsSource,
      zIndex: 10,
      style: (feature) =>
        dgpsPointStyle(
          feature as Feature<Geometry>,
          dgpsFilterRef.current.pending,
          dgpsFilterRef.current.uploaded,
        ),
    });
    dgpsLayerRef.current = dgpsLayer;

    const capturedSource = new VectorSource();
    const capturedLayer = new VectorLayer({
      source: capturedSource,
      zIndex: 11,
      style: (feature) =>
        new Style({
          image: new CircleStyle({
            radius: 7,
            fill: new Fill({ color: feature.get("synced") ? "#10b981" : "#f59e0b" }),
            stroke: new Stroke({ color: "#ffffff", width: 2 }),
          }),
        }),
    });
    capturedLayerRef.current = capturedLayer;

    const map = new Map({
      target,
      controls: defaultControls({ zoom: false, attribution: false }),
      layers: [basemapCarto, basemapOSM, basemapImagery, parcelLayer, dgpsLayer, capturedLayer],
      view: new View({
        center: fromLonLat(dataset.cadastralView.center),
        zoom: dataset.cadastralView.zoom,
        minZoom: 14,
        maxZoom: 20,
      }),
    });

    map.once("rendercomplete", () => {
      const extent = parcelSource.getExtent();
      if (extent && extent.every((v) => Number.isFinite(v))) {
        map.getView().fit(extent, { padding: [36, 36, 36, 36], duration: 400, maxZoom: 19.2 });
      }
    });

    map.on("singleclick", (event) => {
      const feature = map.forEachFeatureAtPixel(
        event.pixel,
        (f) => f,
        { layerFilter: (layer) => layer === parcelLayer },
      ) as Feature<Geometry> | undefined;

      if (feature) {
        const id = String(feature.get("id") ?? feature.getId() ?? "");
        if (id) onParcelClickRef.current(id);
      }
    });

    mapRef.current = map;

    return () => {
      map.setTarget(undefined);
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const layers = basemapLayersRef.current;
    if (!layers["basemap-carto"]) return;
    (Object.keys(layers) as MobileBasemapId[]).forEach((id) => {
      layers[id].setVisible(id === basemapId);
    });
  }, [basemapId]);

  useEffect(() => {
    parcelLayerRef.current?.setVisible(showParcels);
  }, [showParcels]);

  useEffect(() => {
    dgpsLayerRef.current?.setVisible(showDgps);
    capturedLayerRef.current?.setVisible(showDgps);
  }, [showDgps]);

  useEffect(() => {
    const layer = dgpsLayerRef.current;
    if (!layer) return;
    layer.setStyle((feature) =>
      dgpsPointStyle(feature as Feature<Geometry>, dgpsShowPending, dgpsShowUploaded),
    );
    layer.changed();
  }, [dgpsShowPending, dgpsShowUploaded]);

  useEffect(() => {
    const layer = capturedLayerRef.current;
    const source = layer?.getSource();
    if (!source) return;

    source.clear();
    const format = new GeoJSON();
    const features = format.readFeatures(gnssToFeatures(gnssPoints), {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    });
    source.addFeatures(features);
  }, [gnssPoints]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    requestAnimationFrame(() => map.updateSize());
  });

  return <div ref={containerRef} className="h-full w-full touch-none bg-slate-200" />;
}
