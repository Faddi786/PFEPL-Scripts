/**
 * DoSLR WebGIS - OpenLayers map engine with edit/analysis tools.
 */
const MapEngine = (function () {
  "use strict";

  const STYLES = {
    parcelBaseFill: "rgba(180,180,180,0.20)",
    parcelSelectedFill: "rgba(0,0,0,0.28)",
    parcelBaseStroke: "#3a3a3a",
    parcelSelectedStroke: "#000000",
  };

  let map;
  let selectInteraction;
  let currentMode = "select";
  let onSelectCb = null;
  let onContextMenuCb = null;
  let onModeChangeCb = null;
  let onMeasureUpdateCb = null;
  let showAdminLabels = true;

  const layers = {};
  const basemaps = {};
  let activeBasemap = "basemap-osm";
  let activeInteractions = [];

  function readGeoJSON(key) {
    return new ol.format.GeoJSON().readFeatures(MOCK_DATA.geojson[key], {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    });
  }

  function adminStyle(level) {
    const cfg = {
      region: { stroke: "#111", width: 2.2, fill: "rgba(0,0,0,0.03)" },
      taluk: { stroke: "#333", width: 1.8, fill: "rgba(0,0,0,0.02)" },
      village: { stroke: "#666", width: 1.4, fill: "rgba(0,0,0,0.015)" },
      ward: { stroke: "#888", width: 1.2, fill: "rgba(0,0,0,0.01)" },
    }[level] || { stroke: "#444", width: 1.2, fill: "rgba(0,0,0,0.01)" };
    return function (feature) {
      return new ol.style.Style({
        stroke: new ol.style.Stroke({ color: cfg.stroke, width: cfg.width, lineDash: level === "region" ? [8, 6] : undefined }),
        fill: new ol.style.Fill({ color: cfg.fill }),
        text: showAdminLabels
          ? new ol.style.Text({
              text: feature.get("name") || "",
              font: "600 11px Segoe UI,sans-serif",
              fill: new ol.style.Fill({ color: "#111" }),
              stroke: new ol.style.Stroke({ color: "#fff", width: 3 }),
              overflow: true,
            })
          : undefined,
      });
    };
  }

  function parcelStyle(feature, resolution) {
    const selected = !!feature.get("selected");
    return new ol.style.Style({
      fill: new ol.style.Fill({ color: selected ? STYLES.parcelSelectedFill : STYLES.parcelBaseFill }),
      stroke: new ol.style.Stroke({ color: selected ? STYLES.parcelSelectedStroke : STYLES.parcelBaseStroke, width: selected ? 2.2 : 1.1 }),
      text: resolution < 4
        ? new ol.style.Text({
            text: feature.get("surveyNo") || "",
            font: "600 9px ui-monospace,Consolas,monospace",
            fill: new ol.style.Fill({ color: "#111" }),
            stroke: new ol.style.Stroke({ color: "#fff", width: 2 }),
            overflow: true,
          })
        : undefined,
    });
  }

  function makeVectorLayer(id, features, styleFn, zIndex) {
    const source = new ol.source.Vector({ features: features || [] });
    const layer = new ol.layer.Vector({ source: source, style: styleFn, visible: true, opacity: 1, zIndex: zIndex || 10 });
    layer.set("layerId", id);
    layers[id] = layer;
    return layer;
  }

  function initBasemaps() {
    basemaps["basemap-osm"] = new ol.layer.Tile({ source: new ol.source.OSM(), visible: true, zIndex: 0 });
    basemaps["basemap-imagery"] = new ol.layer.Tile({
      source: new ol.source.XYZ({
        url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attributions: "Esri World Imagery",
      }),
      visible: false,
      zIndex: 0,
    });
    basemaps["basemap-carto"] = new ol.layer.Tile({
      source: new ol.source.XYZ({
        url: "https://{a-c}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        attributions: "Carto",
      }),
      visible: false,
      zIndex: 0,
    });
    Object.keys(basemaps).forEach(function (id) { basemaps[id].set("layerId", id); });
  }

  function initOverlays() {
    makeVectorLayer("region", readGeoJSON("region"), adminStyle("region"), 4);
    makeVectorLayer("taluk", readGeoJSON("taluk"), adminStyle("taluk"), 5);
    makeVectorLayer("village", readGeoJSON("village"), adminStyle("village"), 6);
    makeVectorLayer("ward", readGeoJSON("ward"), adminStyle("ward"), 7);

    makeVectorLayer("fmb", readGeoJSON("fmb"), function () {
      return new ol.style.Style({
        stroke: new ol.style.Stroke({ color: "#222", width: 1.8, lineDash: [10, 6] }),
        fill: new ol.style.Fill({ color: "rgba(0,0,0,0.01)" }),
      });
    }, 10);

    makeVectorLayer("ortho", readGeoJSON("ortho"), function () {
      return new ol.style.Style({
        fill: new ol.style.Fill({ color: "rgba(80,80,80,0.20)" }),
        stroke: new ol.style.Stroke({ color: "#666", width: 1.0 }),
      });
    }, 3);

    makeVectorLayer("parcels", readGeoJSON("parcels"), parcelStyle, 20);

    makeVectorLayer("variance", readGeoJSON("variance"), function (feature) {
      const band = feature.get("band") || "green";
      const shades = { green: "rgba(120,120,120,0.23)", amber: "rgba(90,90,90,0.28)", red: "rgba(40,40,40,0.33)" };
      return new ol.style.Style({
        fill: new ol.style.Fill({ color: shades[band] || shades.green }),
        stroke: new ol.style.Stroke({ color: "#333", width: 1, lineDash: [4, 4] }),
      });
    }, 13);

    makeVectorLayer("collabland", readGeoJSON("collabland"), function () {
      return new ol.style.Style({ stroke: new ol.style.Stroke({ color: "#000", width: 2.2, lineDash: [2, 8] }) });
    }, 12);

    makeVectorLayer("dgps", readGeoJSON("dgps"), function (feature) {
      return new ol.style.Style({
        image: new ol.style.Circle({ radius: 5, fill: new ol.style.Fill({ color: "#000" }), stroke: new ol.style.Stroke({ color: "#fff", width: 1.5 }) }),
        text: new ol.style.Text({
          text: feature.get("id") || "",
          offsetY: -12,
          font: "600 9px ui-monospace,Consolas,monospace",
          fill: new ol.style.Fill({ color: "#111" }),
          stroke: new ol.style.Stroke({ color: "#fff", width: 2 }),
        }),
      });
    }, 24);

    makeVectorLayer("analysis", [], function (feature) {
      const kind = feature.get("kind");
      if (kind === "measure") {
        return new ol.style.Style({
          stroke: new ol.style.Stroke({ color: "#000", width: 2, lineDash: [5, 5] }),
          fill: new ol.style.Fill({ color: "rgba(0,0,0,0.06)" }),
        });
      }
      if (kind === "buffer") {
        return new ol.style.Style({
          stroke: new ol.style.Stroke({ color: "#000", width: 2.5 }),
          fill: new ol.style.Fill({ color: "rgba(0,0,0,0.18)" }),
        });
      }
      return new ol.style.Style({ stroke: new ol.style.Stroke({ color: "#000", width: 2 }), fill: new ol.style.Fill({ color: "rgba(0,0,0,0.05)" }) });
    }, 26);

    applyLayerConfig();
  }

  function applyLayerConfig() {
    MOCK_DATA.layerGroups.forEach(function (group) {
      group.layers.forEach(function (cfg) {
        if (cfg.type === "basemap") return;
        if (cfg.id === "admin-labels") {
          showAdminLabels = cfg.visible !== false;
          ["region", "taluk", "village", "ward"].forEach(function (id) { layers[id].changed(); });
          return;
        }
        const layer = layers[cfg.id];
        if (!layer) return;
        layer.setVisible(cfg.visible !== false);
        layer.setOpacity(cfg.opacity != null ? cfg.opacity : 1);
      });
    });
  }

  function clearAnalysis() {
    layers.analysis.getSource().clear();
  }

  function reloadLayerSource(id) {
    if (!layers[id]) return;
    layers[id].setSource(new ol.source.Vector({ features: readGeoJSON(id) }));
    layers[id].changed();
  }

  function mapFeatureToParcelAttrs(feature) {
    if (!feature) return null;
    const id = feature.get("id");
    const fromMock = MOCK_DATA.getParcelById(id);
    if (fromMock) return Object.assign({}, fromMock);

    const geom = feature.getGeometry();
    const areaSqM = Math.round(geom.getArea ? geom.getArea() : 0);
    return {
      id: id,
      surveyNo: feature.get("surveyNo") || id,
      subDiv: feature.get("subDiv") || "-",
      ulpin: feature.get("ulpin") || "generated",
      village: feature.get("village") || "Village",
      taluk: feature.get("taluk") || "Taluk",
      ward: feature.get("ward") || "Ward",
      region: feature.get("region") || (MOCK_DATA.getCurrentRegion ? MOCK_DATA.getCurrentRegion().label : "Puducherry"),
      owner: feature.get("owner") || "Generated",
      ownerMasked: feature.get("ownerMasked") || "G********",
      areaSqM: areaSqM,
      classification: feature.get("classification") || "Mixed",
      landUse: feature.get("landUse") || "Updated",
      encumbrance: feature.get("encumbrance") || "None",
      fmbSheet: feature.get("fmbSheet") || "FMB",
      status: feature.get("status") || "active",
      varianceBand: feature.get("varianceBand") || "green",
      variancePct: feature.get("variancePct") || 0,
    };
  }

  function emitMode(meta) {
    if (onModeChangeCb) onModeChangeCb(Object.assign({ mode: currentMode }, meta || {}));
  }

  function emitMeasure(label) {
    if (onMeasureUpdateCb) onMeasureUpdateCb(label || "");
  }

  function clearMode() {
    activeInteractions.forEach(function (it) { map.removeInteraction(it); });
    activeInteractions = [];
    currentMode = "select";
    emitMode();
    emitMeasure("Mode: Select");
  }

  function setMode(mode) {
    clearMode();
    currentMode = mode;
    emitMode();
  }

  function markSelected(features) {
    const all = layers.parcels.getSource().getFeatures();
    const selectedSet = new Set((features || []).map(function (f) { return f.get("id"); }));
    all.forEach(function (f) { f.set("selected", selectedSet.has(f.get("id"))); });
    layers.parcels.changed();
    if (onSelectCb) {
      const first = features && features[0] ? mapFeatureToParcelAttrs(features[0]) : null;
      onSelectCb(first);
    }
  }

  function getSelectedParcelFeatures() {
    const flagged = layers.parcels.getSource().getFeatures().filter(function (f) { return !!f.get("selected"); });
    if (flagged.length) return flagged;
    if (selectInteraction) return selectInteraction.getFeatures().getArray();
    return [];
  }

  function countPolygonParts(feature) {
    if (!feature || !feature.geometry) return 0;
    if (feature.geometry.type === "Polygon") return 1;
    if (feature.geometry.type === "MultiPolygon") return feature.geometry.coordinates.length;
    return 0;
  }

  function unionFeatureGroup(features, bufferMeters) {
    if (!features.length) return null;
    const working = features.map(function (feature) {
      let next = feature;
      if (bufferMeters > 0) {
        next = turf.buffer(feature, bufferMeters, { units: "meters" });
      }
      return turf.cleanCoords ? turf.cleanCoords(next) : next;
    }).filter(Boolean);

    if (working.length < 2) return working[0] || null;

    let merged;
    try {
      merged = turf.union(turf.featureCollection(working));
    } catch (err) {
      return null;
    }
    if (!merged) return null;

    if (bufferMeters > 0) {
      try {
        const shrunk = turf.buffer(merged, -bufferMeters * 0.85, { units: "meters" });
        if (shrunk && turf.area(shrunk) > 0.5) merged = shrunk;
      } catch (err) {
        // Keep the buffered union if shrink fails on thin geometry.
      }
    }

    return merged;
  }

  function unionWithGapTolerance(turfFeatures) {
    const buffers = [0, 2, 5, 8, 12, 18, 25, 35];
    let best = null;
    let bestParts = Infinity;

    for (let i = 0; i < buffers.length; i++) {
      const meters = buffers[i];
      const candidate = unionFeatureGroup(turfFeatures, meters);
      if (!candidate) continue;
      const parts = countPolygonParts(candidate);
      if (parts === 1) {
        return { feature: candidate, parts: 1 };
      }
      if (parts < bestParts) {
        best = candidate;
        bestParts = parts;
      }
    }

    return { feature: best, parts: bestParts };
  }

  function copyParcelProps(target, source) {
    [
      "village", "taluk", "ward", "region", "classification", "landUse",
      "owner", "ownerMasked", "status", "fmbSheet", "ulpin", "subDiv", "encumbrance",
    ].forEach(function (key) {
      if (source.get(key) != null) target.set(key, source.get(key));
    });
  }

  function syncMergedParcelToMock(mergedFeature, removedIds) {
    if (!MOCK_DATA.parcelAttrs) return;
    removedIds.forEach(function (id) {
      delete MOCK_DATA.parcelAttrs[id];
      if (Array.isArray(MOCK_DATA.parcels)) {
        MOCK_DATA.parcels = MOCK_DATA.parcels.filter(function (p) { return p.id !== id; });
      }
    });
    const attrs = mapFeatureToParcelAttrs(mergedFeature);
    MOCK_DATA.parcelAttrs[attrs.id] = attrs;
    if (Array.isArray(MOCK_DATA.parcels)) MOCK_DATA.parcels.push(attrs);
  }

  function lineSide(a, b, p) {
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]);
  }

  function intersectSegmentWithLine(s, e, a, b) {
    const dx = e[0] - s[0];
    const dy = e[1] - s[1];
    const lx = b[0] - a[0];
    const ly = b[1] - a[1];
    const denom = dx * ly - dy * lx;
    if (Math.abs(denom) < 1e-12) return null;
    const t = ((a[0] - s[0]) * ly - (a[1] - s[1]) * lx) / denom;
    return [s[0] + t * dx, s[1] + t * dy];
  }

  function clipRingWithLine(ring, a, b, keepLeft) {
    const out = [];
    if (!ring.length) return out;
    for (let i = 0; i < ring.length - 1; i++) {
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
    if (out[0][0] !== out[out.length - 1][0] || out[0][1] !== out[out.length - 1][1]) {
      out.push(out[0]);
    }
    return out;
  }

  function splitFeatureByLine(parcelFeature, lineFeature) {
    const poly = new ol.format.GeoJSON().writeFeatureObject(parcelFeature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
    const line = new ol.format.GeoJSON().writeFeatureObject(lineFeature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });

    const ring = poly.geometry.coordinates[0];
    const lineCoords = line.geometry.coordinates;
    if (!lineCoords || lineCoords.length < 2) return null;
    const a = lineCoords[0];
    const b = lineCoords[lineCoords.length - 1];

    turf.lineSplit(turf.polygonToLine(poly), turf.lineString(lineCoords));

    const left = clipRingWithLine(ring, a, b, true);
    const right = clipRingWithLine(ring, a, b, false);
    if (left.length < 4 || right.length < 4) return null;

    const leftPoly = turf.polygon([left]);
    const rightPoly = turf.polygon([right]);
    if (turf.area(leftPoly) < 4 || turf.area(rightPoly) < 4) return null;

    return [leftPoly, rightPoly];
  }

  function rebuildFeatureFromTurf(turfPolygon, sourceFeature, suffix) {
    const geo = turfPolygon.geometry;
    const olFeature = new ol.format.GeoJSON().readFeature({ type: "Feature", properties: {}, geometry: geo }, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    });

    const newId = sourceFeature.get("id") + suffix;
    const newSurvey = (sourceFeature.get("surveyNo") || sourceFeature.get("id")) + suffix;
    olFeature.set("id", newId);
    olFeature.set("surveyNo", newSurvey);

    ["village", "taluk", "ward", "region", "classification", "landUse", "owner", "ownerMasked", "status", "fmbSheet"].forEach(function (k) {
      if (sourceFeature.get(k) != null) olFeature.set(k, sourceFeature.get(k));
    });

    const area = Math.round(olFeature.getGeometry().getArea());
    olFeature.set("areaSqM", area);
    return olFeature;
  }

  function splitParcelWithLine(lineFeature) {
    const selected = getSelectedParcelFeatures();
    let target = selected[0] || null;
    if (!target) {
      target = layers.parcels.getSource().getFeatures().find(function (f) {
        return f.getGeometry().intersectsExtent(lineFeature.getGeometry().getExtent());
      });
    }
    if (!target) return { ok: false, reason: "Select a parcel before split." };

    const split = splitFeatureByLine(target, lineFeature);
    if (!split) return { ok: false, reason: "Split line does not create valid polygons." };

    const source = layers.parcels.getSource();
    const leftFeature = rebuildFeatureFromTurf(split[0], target, "A");
    const rightFeature = rebuildFeatureFromTurf(split[1], target, "B");

    source.removeFeature(target);
    source.addFeatures([leftFeature, rightFeature]);

    selectInteraction.getFeatures().clear();
    selectInteraction.getFeatures().push(leftFeature);
    markSelected([leftFeature]);

    return { ok: true, created: [mapFeatureToParcelAttrs(leftFeature), mapFeatureToParcelAttrs(rightFeature)] };
  }

  function autoSubdivideSelectedParcel() {
    const selected = getSelectedParcelFeatures();
    if (!selected.length) return { ok: false, reason: "Select a parcel before subdivide." };
    const parcelFeature = selected[0];
    const turfFeature = new ol.format.GeoJSON().writeFeatureObject(parcelFeature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
    const bbox = turf.bbox(turfFeature);
    const cx = (bbox[0] + bbox[2]) / 2;
    const line = turf.lineString([[cx, bbox[1] - 0.001], [cx, bbox[3] + 0.001]]);
    const lineFeature = new ol.format.GeoJSON().readFeature(line, { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" });
    return splitParcelWithLine(lineFeature);
  }

  function amalgamateSelected() {
    const selected = getSelectedParcelFeatures();
    if (selected.length < 2) return { ok: false, reason: "Select at least two parcels for amalgamation." };

    const turfFeatures = selected.map(function (f) {
      return new ol.format.GeoJSON().writeFeatureObject(f, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
    });

    let unionResult;
    try {
      unionResult = unionWithGapTolerance(turfFeatures);
    } catch (err) {
      return { ok: false, reason: "Union failed: " + (err.message || "geometry error") };
    }

    const unioned = unionResult && unionResult.feature;
    if (!unioned) return { ok: false, reason: "Union failed." };
    if (unionResult.parts > 1) {
      return {
        ok: false,
        reason: "Selected parcels are too far apart. Choose adjacent plots with small gaps.",
      };
    }

    const source = layers.parcels.getSource();
    const merged = new ol.format.GeoJSON().readFeature(unioned, { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" });
    const mergedId = selected[0].get("id").replace(/-P-/, "-M-") + "-" + Date.now().toString().slice(-4);
    const mergedSurvey = "MERGED-" + String(Math.max(1, selected.length)).padStart(2, "0") + selected[0].get("surveyNo");

    merged.set("id", mergedId);
    merged.set("surveyNo", mergedSurvey);
    merged.set("selected", true);
    copyParcelProps(merged, selected[0]);

    const mergedArea = Math.round(merged.getGeometry().getArea());
    const summedArea = selected.reduce(function (sum, f) { return sum + Number(f.get("areaSqM") || 0); }, 0);
    merged.set("areaSqM", mergedArea > 0 ? mergedArea : summedArea);
    merged.set("status", "mutation_pending");

    const removedIds = selected.map(function (f) { return f.get("id"); });
    selected.forEach(function (f) { source.removeFeature(f); });
    source.addFeature(merged);
    syncMergedParcelToMock(merged, removedIds);

    selectInteraction.getFeatures().clear();
    selectInteraction.getFeatures().push(merged);
    markSelected([merged]);
    layers.parcels.changed();

    return { ok: true, merged: mapFeatureToParcelAttrs(merged) };
  }

  function performSpatialQuery(drawFeature) {
    const query = new ol.format.GeoJSON().writeFeatureObject(drawFeature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
    const hits = layers.parcels.getSource().getFeatures().filter(function (f) {
      const parcel = new ol.format.GeoJSON().writeFeatureObject(f, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
      return turf.booleanIntersects(query, parcel);
    });

    selectInteraction.getFeatures().clear();
    hits.forEach(function (f) { selectInteraction.getFeatures().push(f); });
    markSelected(hits);
    return hits.map(mapFeatureToParcelAttrs);
  }

  function startVertexEdit() {
    setMode("vertex-edit");
    const modify = new ol.interaction.Modify({ source: layers.parcels.getSource() });
    const snap = new ol.interaction.Snap({ source: layers.parcels.getSource() });
    modify.on("modifyend", function () {
      const selected = getSelectedParcelFeatures();
      emitMeasure(selected.length ? "Vertex edit saved" : "Vertex edit active");
    });
    [modify, snap].forEach(function (it) {
      map.addInteraction(it);
      activeInteractions.push(it);
    });
    emitMeasure("Vertex edit active");
  }

  function startSplit() {
    setMode("split");
    const draw = new ol.interaction.Draw({ source: layers.analysis.getSource(), type: "LineString" });
    draw.on("drawend", function (evt) {
      const result = splitParcelWithLine(evt.feature);
      layers.analysis.getSource().clear();
      emitMeasure(result.ok ? "Parcel split completed" : "Split failed: " + result.reason);
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    emitMeasure("Draw split line across parcel");
  }

  function startAmalgamate() {
    setMode("amalgamate");
    map.once("singleclick", function () {
      emitMeasure("Select parcels then run amalgamation");
    });
    emitMeasure("Select multiple parcels with Shift+click");
  }

  function setupMeasureDraw(type, labelBuilder, options) {
    setMode(type);
    clearAnalysis();
    const draw = new ol.interaction.Draw(Object.assign({ source: layers.analysis.getSource(), type: options.drawType }, options.extra || {}));
    draw.on("drawstart", function () { clearAnalysis(); });
    draw.on("drawend", function (evt) {
      evt.feature.set("kind", "measure");
      emitMeasure(labelBuilder(evt.feature.getGeometry()));
    });
    draw.on("drawabort", function () { emitMeasure("Measure cancelled"); });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    emitMeasure(options.hint);
  }

  function startMeasureDistance() {
    setupMeasureDraw("measure-distance", function (geom) {
      const meters = geom.getLength();
      return "Distance: " + (meters >= 1000 ? (meters / 1000).toFixed(3) + " km" : meters.toFixed(2) + " m");
    }, { drawType: "LineString", hint: "Draw line for distance" });
  }

  function startMeasureArea() {
    setupMeasureDraw("measure-area", function (geom) {
      const area = geom.getArea();
      return "Area: " + (area >= 1000000 ? (area / 1000000).toFixed(3) + " km²" : area.toFixed(2) + " m²");
    }, { drawType: "Polygon", hint: "Draw polygon for area" });
  }

  function startMeasureBearing() {
    setupMeasureDraw("measure-bearing", function (geom) {
      const c = geom.getCoordinates();
      if (c.length < 2) return "Bearing: -";
      const from = ol.proj.toLonLat(c[0]);
      const to = ol.proj.toLonLat(c[c.length - 1]);
      const brg = turf.bearing(turf.point(from), turf.point(to));
      const normalized = ((brg % 360) + 360) % 360;
      return "Bearing: " + normalized.toFixed(2) + "°";
    }, { drawType: "LineString", hint: "Draw 2-point line for bearing", extra: { maxPoints: 2 } });
  }

  function startBuffer() {
    setMode("buffer");
    clearAnalysis();
    const draw = new ol.interaction.Draw({ source: layers.analysis.getSource(), type: "Point" });
    draw.on("drawend", function (evt) {
      const radiusInput = window.prompt("Buffer radius in meters", "50");
      const radius = Number(radiusInput);
      if (!Number.isFinite(radius) || radius <= 0) {
        emitMeasure("Invalid buffer radius");
        layers.analysis.getSource().clear();
        return;
      }
      const point = new ol.format.GeoJSON().writeFeatureObject(evt.feature, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
      const buffered = turf.buffer(point, radius, { units: "meters" });
      const bufferFeature = new ol.format.GeoJSON().readFeature(buffered, { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" });
      bufferFeature.set("kind", "buffer");
      layers.analysis.getSource().clear();
      layers.analysis.getSource().addFeature(bufferFeature);
      emitMeasure("Buffer created: " + radius.toFixed(2) + " m");
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    emitMeasure("Click map to create buffer");
  }

  function startSpatialQuery() {
    setMode("spatial-query");
    clearAnalysis();
    const draw = new ol.interaction.Draw({ source: layers.analysis.getSource(), type: "Polygon" });
    draw.on("drawend", function (evt) {
      const hits = performSpatialQuery(evt.feature);
      emitMeasure("Spatial query matched " + hits.length + " parcel(s)");
      layers.analysis.getSource().clear();
    });
    map.addInteraction(draw);
    activeInteractions.push(draw);
    emitMeasure("Draw query polygon");
  }

  function startRubberSheet() {
    setMode("rubber-sheet");
    const features = selectInteraction.getFeatures();
    if (!features.getLength()) {
      emitMeasure("Select parcel(s) first, then run rubber sheet");
      return;
    }
    const translate = new ol.interaction.Translate({ features: features });
    const modify = new ol.interaction.Modify({ features: features });
    [translate, modify].forEach(function (it) {
      map.addInteraction(it);
      activeInteractions.push(it);
    });
    emitMeasure("Rubber-sheet active: drag selected geometry");
  }

  function startGeoref() {
    setMode("georef");
    const modify = new ol.interaction.Modify({ source: layers.dgps.getSource() });
    map.addInteraction(modify);
    activeInteractions.push(modify);
    emitMeasure("Georef active: drag DGPS points");
  }

  function getParcelAtPixel(pixel) {
    const feature = map.forEachFeatureAtPixel(pixel, function (f, layer) {
      return layer === layers.parcels ? f : null;
    });
    return feature ? mapFeatureToParcelAttrs(feature) : null;
  }

  function getSelectedParcels() {
    return getSelectedParcelFeatures().map(mapFeatureToParcelAttrs);
  }

  function selectParcelById(id) {
    const source = layers.parcels.getSource();
    const feature = source.getFeatures().find(function (f) { return f.get("id") === id; });
    if (!feature) return;
    selectInteraction.getFeatures().clear();
    selectInteraction.getFeatures().push(feature);
    markSelected([feature]);
    map.getView().fit(feature.getGeometry().getExtent(), { padding: [70, 70, 70, 280], maxZoom: 18, duration: 250 });
  }

  function setBasemap(id) {
    if (!basemaps[id]) return;
    activeBasemap = id;
    Object.keys(basemaps).forEach(function (key) { basemaps[key].setVisible(key === id); });
  }

  function setLayerVisible(id, visible) {
    if (basemaps[id]) {
      if (visible) setBasemap(id);
      return;
    }
    if (id === "admin-labels") {
      showAdminLabels = !!visible;
      ["region", "taluk", "village", "ward"].forEach(function (k) { layers[k].changed(); });
      return;
    }
    if (layers[id]) layers[id].setVisible(!!visible);
  }

  function getLayerVisible(id) {
    if (id === "admin-labels") return showAdminLabels;
    const layer = layers[id] || basemaps[id];
    return layer ? layer.getVisible() : false;
  }

  function zoomHome() {
    map.getView().animate({ center: ol.proj.fromLonLat(MOCK_DATA.center), zoom: MOCK_DATA.zoom, duration: 350 });
  }

  function switchRegion(regionKey) {
    if (!MOCK_DATA.setRegion || !MOCK_DATA.setRegion(regionKey)) {
      return { ok: false, reason: "Unknown region." };
    }

    ["ortho", "region", "taluk", "village", "ward", "fmb", "collabland", "variance", "dgps", "parcels"].forEach(reloadLayerSource);
    applyLayerConfig();

    if (selectInteraction) selectInteraction.getFeatures().clear();
    markSelected([]);
    clearAnalysis();
    zoomHome();
    return { ok: true, region: MOCK_DATA.getCurrentRegion ? MOCK_DATA.getCurrentRegion() : null };
  }

  function getRegionCatalog() {
    return MOCK_DATA.getRegions ? MOCK_DATA.getRegions() : [];
  }

  function getCurrentRegion() {
    return MOCK_DATA.getCurrentRegion ? MOCK_DATA.getCurrentRegion() : null;
  }

  function exportSelectionGeoJSON() {
    const selected = getSelectedParcelFeatures();
    if (!selected.length) return null;
    return new ol.format.GeoJSON().writeFeaturesObject(selected, { featureProjection: "EPSG:3857", dataProjection: "EPSG:4326" });
  }

  function init(containerId) {
    initBasemaps();
    initOverlays();

    map = new ol.Map({
      target: containerId,
      layers: [
        basemaps["basemap-osm"],
        basemaps["basemap-imagery"],
        basemaps["basemap-carto"],
        layers.ortho,
        layers.region,
        layers.taluk,
        layers.village,
        layers.ward,
        layers.fmb,
        layers.collabland,
        layers.variance,
        layers.parcels,
        layers.dgps,
        layers.analysis,
      ],
      view: new ol.View({ center: ol.proj.fromLonLat(MOCK_DATA.center), zoom: MOCK_DATA.zoom, maxZoom: 20 }),
      controls: ol.control.defaults.defaults({ attribution: true, zoom: true, rotate: false }),
    });

    selectInteraction = new ol.interaction.Select({
      layers: [layers.parcels],
      style: null,
      hitTolerance: 6,
      toggleCondition: ol.events.condition.shiftKeyOnly,
      multi: true,
    });

    selectInteraction.on("select", function (evt) {
      const features = selectInteraction.getFeatures().getArray();
      markSelected(features);
      if (features.length && onSelectCb) onSelectCb(mapFeatureToParcelAttrs(features[features.length - 1]));
      if (!features.length && onSelectCb) onSelectCb(null);
    });

    map.addInteraction(selectInteraction);

    map.on("pointermove", function (evt) {
      const hit = map.hasFeatureAtPixel(evt.pixel, { layerFilter: function (layer) { return layer === layers.parcels; } });
      map.getTargetElement().style.cursor = hit ? "pointer" : "";
    });

    map.getViewport().addEventListener("contextmenu", function (evt) {
      evt.preventDefault();
      const pixel = map.getEventPixel(evt);
      const parcel = getParcelAtPixel(pixel);
      if (onContextMenuCb) {
        onContextMenuCb({
          parcel: parcel,
          pixel: pixel,
          coordinate: map.getCoordinateFromPixel(pixel),
          clientX: evt.clientX,
          clientY: evt.clientY,
        });
      }
    });

    emitMeasure("Mode: Select");
    return map;
  }

  function onParcelSelect(cb) { onSelectCb = cb; }
  function onContextMenu(cb) { onContextMenuCb = cb; }
  function onModeChange(cb) { onModeChangeCb = cb; }
  function onMeasureUpdate(cb) { onMeasureUpdateCb = cb; }

  return {
    init: init,
    getMap: function () { return map; },
    getActiveBasemap: function () { return activeBasemap; },
    setBasemap: setBasemap,
    switchRegion: switchRegion,
    getRegionCatalog: getRegionCatalog,
    getCurrentRegion: getCurrentRegion,
    setLayerVisible: setLayerVisible,
    getLayerVisible: getLayerVisible,
    setMode: setMode,
    clearMode: clearMode,
    startVertexEdit: startVertexEdit,
    startSplit: startSplit,
    startAmalgamate: startAmalgamate,
    startMeasureDistance: startMeasureDistance,
    startMeasureArea: startMeasureArea,
    startMeasureBearing: startMeasureBearing,
    startBuffer: startBuffer,
    startSpatialQuery: startSpatialQuery,
    startRubberSheet: startRubberSheet,
    startGeoref: startGeoref,
    getParcelAtPixel: getParcelAtPixel,
    getSelectedParcels: getSelectedParcels,
    amalgamateSelected: amalgamateSelected,
    splitParcelWithLine: splitParcelWithLine,
    autoSubdivideSelectedParcel: autoSubdivideSelectedParcel,
    selectParcelById: selectParcelById,
    zoomHome: zoomHome,
    exportSelectionGeoJSON: exportSelectionGeoJSON,
    onParcelSelect: onParcelSelect,
    onContextMenu: onContextMenu,
    onModeChange: onModeChange,
    onMeasureUpdate: onMeasureUpdate,
  };
})();
