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
import Select from "ol/interaction/Select";
import Modify from "ol/interaction/Modify";
import Draw from "ol/interaction/Draw";
import Snap from "ol/interaction/Snap";
import type Feature from "ol/Feature";
import type Geometry from "ol/geom/Geometry";
import type { Polygon } from "ol/geom";
import type { Coordinate } from "ol/coordinate";
import * as turf from "@turf/turf";
import type { RegionDataset } from "../data/mockData";

type LayerId =
  | "region"
  | "taluk"
  | "village"
  | "ward"
  | "fmb"
  | "parcels"
  | "variance"
  | "dgps"
  | "collabland"
  | "ortho";

export type MapTool =
  | "none"
  | "vertex-edit"
  | "split"
  | "amalgamate"
  | "measure-distance"
  | "buffer";

type Callbacks = {
  onParcelContext?: (parcel: Record<string, any>, pixel: Coordinate) => void;
  onToast?: (message: string) => void;
  onSelectionChange?: (parcel: Record<string, any> | null) => void;
};

type EngineInstance = {
  map: Map;
  setDataset: (dataset: RegionDataset) => void;
  setBasemap: (id: string) => void;
  setLayerVisibility: (id: string, visible: boolean) => void;
  setTool: (tool: MapTool) => void;
  resetTools: (silent?: boolean) => void;
  runAmalgamation: () => { ok: boolean; reason?: string };
  highlightParcels: (ids: string[]) => void;
  clearHighlights: () => void;
  clearInteractions: () => void;
  dispose: () => void;
};

function parcelToRecord(feature: Feature<Geometry>): Record<string, unknown> {
  const props = feature.getProperties();
  const { geometry, ...rest } = props as Record<string, unknown>;
  void geometry;
  return rest;
}

function countPolygonParts(feature: any) {
  if (!feature?.geometry) return 0;
  if (feature.geometry.type === "Polygon") return 1;
  if (feature.geometry.type === "MultiPolygon") return feature.geometry.coordinates.length;
  return 0;
}

function unionFeatureGroup(features: GeoJSON.Feature[], bufferMeters: number) {
  if (!features.length) return null;
  const working = features
    .map((feature) => {
      if (bufferMeters <= 0) return feature;
      return turf.buffer(feature, bufferMeters, { units: "meters" }) as GeoJSON.Feature;
    })
    .map((feature) => (turf.cleanCoords ? (turf.cleanCoords(feature) as GeoJSON.Feature) : feature))
    .filter(Boolean);

  if (working.length < 2) return working[0] ?? null;

  try {
    const merged = turf.union(turf.featureCollection(working as any) as any);
    if (!merged) return null;
    if (bufferMeters <= 0) return merged as GeoJSON.Feature;
    try {
      const shrunk = turf.buffer(merged, -bufferMeters * 0.85, { units: "meters" });
      if (shrunk && turf.area(shrunk) > 0.5) return shrunk as GeoJSON.Feature;
    } catch {
      // Keep buffered union if shrink fails.
    }
    return merged as GeoJSON.Feature;
  } catch {
    return null;
  }
}

function unionWithGapTolerance(features: GeoJSON.Feature[]) {
  const buffers = [0, 2, 5, 8, 12, 18, 25, 35];
  let best: GeoJSON.Feature | null = null;
  let bestParts = Number.POSITIVE_INFINITY;

  for (const bufferMeters of buffers) {
    const candidate = unionFeatureGroup(features, bufferMeters);
    if (!candidate) continue;
    const parts = countPolygonParts(candidate);
    if (parts === 1) return { feature: candidate, parts: 1 };
    if (parts < bestParts) {
      best = candidate;
      bestParts = parts;
    }
  }

  return { feature: best, parts: bestParts };
}

function lineSide(a: [number, number], b: [number, number], p: [number, number]) {
  return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]);
}

function intersectSegmentWithLine(
  s: [number, number],
  e: [number, number],
  a: [number, number],
  b: [number, number],
): [number, number] | null {
  const dx = e[0] - s[0];
  const dy = e[1] - s[1];
  const lx = b[0] - a[0];
  const ly = b[1] - a[1];
  const denom = dx * ly - dy * lx;
  if (Math.abs(denom) < 1e-12) return null;
  const t = ((a[0] - s[0]) * ly - (a[1] - s[1]) * lx) / denom;
  return [s[0] + t * dx, s[1] + t * dy];
}

function clipRingWithLine(
  ring: [number, number][],
  a: [number, number],
  b: [number, number],
  keepLeft: boolean,
): [number, number][] {
  const out: [number, number][] = [];
  if (!ring.length) return out;

  for (let i = 0; i < ring.length - 1; i += 1) {
    const s = ring[i];
    const e = ring[i + 1];
    const sIn = keepLeft ? lineSide(a, b, s) >= 0 : lineSide(a, b, s) <= 0;
    const eIn = keepLeft ? lineSide(a, b, e) >= 0 : lineSide(a, b, e) <= 0;

    if (sIn && eIn) {
      out.push(e);
    } else if (sIn && !eIn) {
      const ip = intersectSegmentWithLine(s, e, a, b);
      if (ip) out.push(ip);
    } else if (!sIn && eIn) {
      const ip = intersectSegmentWithLine(s, e, a, b);
      if (ip) out.push(ip);
      out.push(e);
    }
  }

  if (!out.length) return out;
  const first = out[0];
  const last = out[out.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) out.push(first);
  return out;
}

function splitPolygonByLine(
  parcelGeo: GeoJSON.Feature<GeoJSON.Polygon>,
  lineCoords: [number, number][],
): [GeoJSON.Feature<GeoJSON.Polygon>, GeoJSON.Feature<GeoJSON.Polygon>] | null {
  if (lineCoords.length < 2) return null;

  const ring = parcelGeo.geometry.coordinates[0] as [number, number][];
  const a = lineCoords[0];
  const b = lineCoords[lineCoords.length - 1];
  const leftRing = clipRingWithLine(ring, a, b, true);
  const rightRing = clipRingWithLine(ring, a, b, false);
  if (leftRing.length < 4 || rightRing.length < 4) return null;

  const leftPoly = turf.polygon([leftRing]);
  const rightPoly = turf.polygon([rightRing]);
  if (turf.area(leftPoly) < 4 || turf.area(rightPoly) < 4) return null;

  return [leftPoly, rightPoly];
}

export function createMapEngine(target: HTMLElement, dataset: RegionDataset, callbacks: Callbacks = {}): EngineInstance {
  const format = new GeoJSON();
  const analysisSource = new VectorSource();
  const parcelSource = new VectorSource();
  const genericSources: Record<LayerId, VectorSource> = {
    region: new VectorSource(),
    taluk: new VectorSource(),
    village: new VectorSource(),
    ward: new VectorSource(),
    fmb: new VectorSource(),
    parcels: parcelSource,
    variance: new VectorSource(),
    dgps: new VectorSource(),
    collabland: new VectorSource(),
    ortho: new VectorSource(),
  };

  const basemapCarto = new TileLayer({
    source: new XYZ({
      url: "https://{a-d}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
      attributions: "&copy; OpenStreetMap contributors &copy; CARTO",
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

  const styleByLayer: Record<LayerId | "analysis", Style> = {
    region: new Style({ stroke: new Stroke({ color: "#475569", width: 2 }), fill: new Fill({ color: "rgba(148,163,184,0.08)" }) }),
    taluk: new Style({ stroke: new Stroke({ color: "#64748b", width: 1.6 }), fill: new Fill({ color: "rgba(100,116,139,0.04)" }) }),
    village: new Style({ stroke: new Stroke({ color: "#0f766e", width: 1.2 }), fill: new Fill({ color: "rgba(20,184,166,0.05)" }) }),
    ward: new Style({ stroke: new Stroke({ color: "#3b82f6", width: 1.1 }), fill: new Fill({ color: "rgba(59,130,246,0.05)" }) }),
    fmb: new Style({ stroke: new Stroke({ color: "#64748b", width: 1.1, lineDash: [5, 5] }), fill: new Fill({ color: "rgba(100,116,139,0.04)" }) }),
    parcels: new Style({ stroke: new Stroke({ color: "#0f172a", width: 1.1 }), fill: new Fill({ color: "rgba(255,255,255,0.25)" }) }),
    variance: new Style({ stroke: new Stroke({ color: "#334155", width: 0.8 }), fill: new Fill({ color: "rgba(251,191,36,0.18)" }) }),
    dgps: new Style({
      image: new CircleStyle({ radius: 5, fill: new Fill({ color: "#0ea5e9" }), stroke: new Stroke({ color: "#ffffff", width: 1.2 }) }),
    }),
    collabland: new Style({ stroke: new Stroke({ color: "#f59e0b", width: 2.5 }) }),
    ortho: new Style({ stroke: new Stroke({ color: "#94a3b8", width: 0.8 }), fill: new Fill({ color: "rgba(148,163,184,0.06)" }) }),
    analysis: new Style({
      stroke: new Stroke({ color: "#111827", width: 2, lineDash: [8, 6] }),
      fill: new Fill({ color: "rgba(59,130,246,0.08)" }),
      image: new CircleStyle({ radius: 4, fill: new Fill({ color: "#2563eb" }), stroke: new Stroke({ color: "#fff", width: 1.2 }) }),
    }),
  };

  let parcelsLayerVisible = true;
  let varianceLayerVisible = false;

  const variancePalette = {
    green: { fill: "rgba(34,197,94,0.50)", stroke: "#15803d" },
    amber: { fill: "rgba(245,158,11,0.52)", stroke: "#b45309" },
    red: { fill: "rgba(239,68,68,0.52)", stroke: "#b91c1c" },
  } as const;

  function parcelLabelStyle(feature: Feature<Geometry>, resolution: number) {
    if (!parcelsLayerVisible || resolution >= 5) return undefined;
    const surveyNo = String(feature.get("surveyNo") || "");
    if (!surveyNo) return undefined;
    return new Text({
      text: surveyNo,
      font: "600 9px ui-monospace,Consolas,monospace",
      fill: new Fill({ color: "#111" }),
      stroke: new Stroke({ color: "#fff", width: 2 }),
      overflow: true,
    });
  }

  function varianceLabelStyle(feature: Feature<Geometry>, resolution: number) {
    if (!varianceLayerVisible || parcelsLayerVisible || resolution >= 5) return undefined;
    const surveyNo = String(feature.get("surveyNo") || "");
    if (!surveyNo) return undefined;
    return new Text({
      text: surveyNo,
      font: "600 9px ui-monospace,Consolas,monospace",
      fill: new Fill({ color: "#111" }),
      stroke: new Stroke({ color: "#fff", width: 2 }),
      overflow: true,
    });
  }

  const layerMap: Record<LayerId | "analysis", VectorLayer<VectorSource>> = {
    region: new VectorLayer({ source: genericSources.region, style: styleByLayer.region, zIndex: 2 }),
    taluk: new VectorLayer({ source: genericSources.taluk, style: styleByLayer.taluk, zIndex: 3 }),
    village: new VectorLayer({ source: genericSources.village, style: styleByLayer.village, zIndex: 4 }),
    ward: new VectorLayer({ source: genericSources.ward, style: styleByLayer.ward, zIndex: 5 }),
    fmb: new VectorLayer({ source: genericSources.fmb, style: styleByLayer.fmb, zIndex: 6 }),
    parcels: new VectorLayer({
      source: genericSources.parcels,
      zIndex: 9,
      style: (feature, resolution) =>
        new Style({
          stroke: new Stroke({
            color: feature.get("selected") ? "#2563eb" : "#0f172a",
            width: feature.get("selected") ? 2.3 : 1.1,
          }),
          fill: new Fill({
            color: feature.get("selected") ? "rgba(59,130,246,0.15)" : "rgba(148,163,184,0.35)",
          }),
          text: parcelLabelStyle(feature as Feature<Geometry>, resolution),
        }),
    }),
    variance: new VectorLayer({
      source: genericSources.variance,
      zIndex: 8,
      style: (feature, resolution) => {
        const band = String(feature.get("band") || "green") as keyof typeof variancePalette;
        const colors = variancePalette[band] ?? variancePalette.green;
        return new Style({
          fill: new Fill({ color: colors.fill }),
          stroke: new Stroke({ color: colors.stroke, width: 1.2 }),
          text: varianceLabelStyle(feature as Feature<Geometry>, resolution),
        });
      },
    }),
    dgps: new VectorLayer({ source: genericSources.dgps, style: styleByLayer.dgps, zIndex: 10 }),
    collabland: new VectorLayer({ source: genericSources.collabland, style: styleByLayer.collabland, zIndex: 8 }),
    ortho: new VectorLayer({ source: genericSources.ortho, style: styleByLayer.ortho, zIndex: 1 }),
    analysis: new VectorLayer({ source: analysisSource, style: styleByLayer.analysis, zIndex: 11 }),
  };

  const map = new Map({
    target,
    controls: defaultControls({ zoom: false, attribution: false }),
    layers: [
      basemapCarto,
      basemapOSM,
      basemapImagery,
      layerMap.ortho,
      layerMap.region,
      layerMap.taluk,
      layerMap.village,
      layerMap.ward,
      layerMap.fmb,
      layerMap.variance,
      layerMap.collabland,
      layerMap.parcels,
      layerMap.dgps,
      layerMap.analysis,
    ],
    view: new View({
      center: fromLonLat(dataset.center),
      zoom: dataset.zoom,
    }),
  });

  const select = new Select({ layers: [layerMap.parcels], style: null, multi: true });
  map.addInteraction(select);

  const activeInteractions: Array<Modify | Draw | Snap> = [];

  function refreshStyledLayers() {
    layerMap.parcels.changed();
    layerMap.variance.changed();
  }

  function clearInteractions() {
    activeInteractions.forEach((interaction) => map.removeInteraction(interaction));
    activeInteractions.length = 0;
    analysisSource.clear();
  }

  function resetTools(silent = false) {
    clearInteractions();
    if (!silent) callbacks.onToast?.("Tools reset");
  }

  function fitToParcels(fallback: RegionDataset) {
    if (fallback.cadastralView) {
      map.getView().animate({
        center: fromLonLat(fallback.cadastralView.center),
        zoom: fallback.cadastralView.zoom,
        duration: 500,
      });
      return;
    }

    const extent = parcelSource.getExtent();
    if (extent && extent.every((value) => Number.isFinite(value))) {
      map.getView().fit(extent, { padding: [28, 28, 28, 28], duration: 450, maxZoom: 19.5 });
      return;
    }
    map.getView().animate({ center: fromLonLat(fallback.center), zoom: fallback.zoom, duration: 450 });
  }

  function loadDataset(next: RegionDataset) {
    (Object.keys(genericSources) as LayerId[]).forEach((layerId) => {
      genericSources[layerId].clear();
      const collection = next.geojson[layerId];
      if (!collection) return;
      const features = format.readFeatures(collection, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      });
      genericSources[layerId].addFeatures(features);
    });
    fitToParcels(next);
  }

  loadDataset(dataset);

  select.on("select", () => {
    const selected = select.getFeatures().getArray();
    const selectedSet = new Set(selected.map((f) => f.get("id")));
    parcelSource.getFeatures().forEach((f) => f.set("selected", selectedSet.has(f.get("id"))));
    callbacks.onSelectionChange?.(selected[0] ? parcelToRecord(selected[0]) : null);
  });

  map.getViewport().addEventListener("contextmenu", (event) => {
    event.preventDefault();
    const pixel = map.getEventPixel(event);
    const parcel = map.forEachFeatureAtPixel(pixel, (feature, layer) => {
      if (layer === layerMap.parcels) return feature;
      return null;
    });
    if (!parcel) return;
    callbacks.onParcelContext?.(parcelToRecord(parcel as Feature<Geometry>), map.getCoordinateFromPixel(pixel));
  });

  function startVertexEdit() {
    clearInteractions();
    const modify = new Modify({ source: parcelSource });
    const snap = new Snap({ source: parcelSource });
    modify.on("modifyend", () => callbacks.onToast?.("Vertex edit saved"));
    map.addInteraction(modify);
    map.addInteraction(snap);
    activeInteractions.push(modify, snap);
    callbacks.onToast?.("Vertex edit active");
  }

  function splitSelectedWithDraw() {
    clearInteractions();
    const draw = new Draw({ source: analysisSource, type: "LineString" });
    draw.on("drawend", (event) => {
      const selected = select.getFeatures().item(0);
      if (!selected) {
        callbacks.onToast?.("Select one parcel before split");
        analysisSource.clear();
        return;
      }
      const parcelGeo = format.writeFeatureObject(selected, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326",
      }) as GeoJSON.Feature<GeoJSON.Polygon>;
      const lineGeo = format.writeFeatureObject(event.feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326",
      }) as GeoJSON.Feature<GeoJSON.LineString>;
      const splitResult = splitPolygonByLine(parcelGeo, lineGeo.geometry.coordinates as [number, number][]);
      if (!splitResult) {
        callbacks.onToast?.("Split failed: line not crossing polygon");
        analysisSource.clear();
        return;
      }

      const sourceId = String(selected.get("id"));
      const sourceSurveyNo = String(selected.get("surveyNo") || sourceId);
      parcelSource.removeFeature(selected);
      select.getFeatures().clear();

      splitResult.forEach((polygon, index) => {
        const suffix = index === 0 ? "A" : "B";
        const feature = format.readFeature(polygon, {
          dataProjection: "EPSG:4326",
          featureProjection: "EPSG:3857",
        }) as Feature<Geometry>;

        Object.keys(parcelGeo.properties ?? {}).forEach((key) => {
          if (parcelGeo.properties?.[key] !== undefined) feature.set(key, parcelGeo.properties[key]);
        });

        feature.set("id", `${sourceId}${suffix}`);
        feature.set("surveyNo", `${sourceSurveyNo}${suffix}`);
        feature.set("areaSqM", Math.round((feature.getGeometry() as Polygon | null)?.getArea() ?? 0));
        feature.set("selected", index === 0);
        parcelSource.addFeature(feature);
        if (index === 0) select.getFeatures().push(feature);
      });
      analysisSource.clear();
      callbacks.onToast?.("Parcel split completed");
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    callbacks.onToast?.("Draw split line across selected parcel");
  }

  function startMeasureDistance() {
    clearInteractions();
    const draw = new Draw({ source: analysisSource, type: "LineString" });
    draw.on("drawend", (event) => {
      const geom = event.feature.getGeometry() as any;
      const length = geom?.getLength?.() ?? 0;
      callbacks.onToast?.(
        `Distance: ${length >= 1000 ? `${(length / 1000).toFixed(2)} km` : `${length.toFixed(2)} m`}`,
      );
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    callbacks.onToast?.("Draw line to measure distance");
  }

  function startBuffer() {
    clearInteractions();
    const draw = new Draw({ source: analysisSource, type: "Point" });
    draw.on("drawend", (event) => {
      const radiusInput = window.prompt("Buffer radius in meters", "60");
      const radius = Number(radiusInput);
      if (!Number.isFinite(radius) || radius <= 0) {
        callbacks.onToast?.("Invalid buffer radius");
        analysisSource.clear();
        return;
      }
      const pointGeo = format.writeFeatureObject(event.feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326",
      }) as GeoJSON.Feature<GeoJSON.Point>;
      const buffered = turf.buffer(pointGeo, radius, { units: "meters" });
      const feature = format.readFeature(buffered, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }) as Feature<Geometry>;
      analysisSource.clear();
      analysisSource.addFeature(feature);
      callbacks.onToast?.(`Buffer created (${radius.toFixed(0)} m)`);
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    callbacks.onToast?.("Click map to create buffer");
  }

  function runAmalgamation() {
    const selected = select.getFeatures().getArray();
    if (selected.length < 2) return { ok: false, reason: "Select at least two parcels for amalgamation." };

    const turfFeatures = selected.map((feature) =>
      format.writeFeatureObject(feature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" }),
    ) as GeoJSON.Feature[];

    const result = unionWithGapTolerance(turfFeatures);
    if (!result.feature) return { ok: false, reason: "Union failed." };
    if (result.parts > 1) {
      return { ok: false, reason: "Parcels are too far apart; select adjacent geometries." };
    }

    const merged = format.readFeature(result.feature, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    }) as Feature<Geometry>;
    const first = selected[0];
    const mergedId = `${first.get("id").replace("-P-", "-M-")}-${Date.now().toString().slice(-4)}`;
    merged.set("id", mergedId);
    merged.set("surveyNo", `MERGED-${first.get("surveyNo")}`);
    merged.set("status", "mutation_pending");
    merged.set("selected", true);
    selected.forEach((feature) => parcelSource.removeFeature(feature));
    parcelSource.addFeature(merged);
    select.getFeatures().clear();
    select.getFeatures().push(merged);
    callbacks.onToast?.("Amalgamation completed");
    return { ok: true };
  }

  function highlightParcels(ids: string[]) {
    select.getFeatures().clear();
    const idSet = new Set(ids.map(String));
    parcelSource.getFeatures().forEach((feature) => {
      feature.set("selected", idSet.has(String(feature.get("id"))));
    });
    refreshStyledLayers();

    const matched = parcelSource.getFeatures().filter((feature) => idSet.has(String(feature.get("id"))));
    if (!matched.length) return;

    let extent = matched[0].getGeometry()?.getExtent();
    matched.slice(1).forEach((feature) => {
      const geometry = feature.getGeometry();
      if (!geometry || !extent) return;
      extent = [
        Math.min(extent[0], geometry.getExtent()[0]),
        Math.min(extent[1], geometry.getExtent()[1]),
        Math.max(extent[2], geometry.getExtent()[2]),
        Math.max(extent[3], geometry.getExtent()[3]),
      ];
    });

    if (extent && extent.every((value) => Number.isFinite(value))) {
      map.getView().fit(extent, { padding: [48, 48, 48, 48], duration: 650, maxZoom: 20 });
    }
  }

  function clearHighlights() {
    select.getFeatures().clear();
    parcelSource.getFeatures().forEach((feature) => feature.set("selected", false));
    refreshStyledLayers();
  }

  return {
    map,
    setDataset: loadDataset,
    setBasemap: (id: string) => {
      basemapCarto.setVisible(id === "basemap-carto");
      basemapOSM.setVisible(id === "basemap-osm");
      basemapImagery.setVisible(id === "basemap-imagery");
    },
    setLayerVisibility: (id: string, visible: boolean) => {
      const layer = layerMap[id as LayerId];
      if (layer) layer.setVisible(visible);
      if (id === "parcels") parcelsLayerVisible = visible;
      if (id === "variance") varianceLayerVisible = visible;
      refreshStyledLayers();
    },
    setTool: (tool: MapTool) => {
      if (tool === "none") {
        resetTools();
        return;
      }
      if (tool === "vertex-edit") startVertexEdit();
      if (tool === "split") splitSelectedWithDraw();
      if (tool === "measure-distance") startMeasureDistance();
      if (tool === "buffer") startBuffer();
      if (tool === "amalgamate") {
        const result = runAmalgamation();
        if (!result.ok && result.reason) callbacks.onToast?.(result.reason);
        return;
      }
    },
    runAmalgamation,
    resetTools,
    highlightParcels,
    clearHighlights,
    clearInteractions,
    dispose: () => {
      clearInteractions();
      map.setTarget(undefined);
    },
  };
}
