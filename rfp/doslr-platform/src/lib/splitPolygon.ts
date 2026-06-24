import {
  buffer,
  difference,
  featureCollection,
  lineIntersect,
  lineString,
  polygonToLine,
} from "@turf/turf";

function asPolygons(geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon): GeoJSON.Feature<GeoJSON.Polygon>[] {
  if (geometry.type === "Polygon") {
    return [{ type: "Feature", properties: {}, geometry }];
  }
  return geometry.coordinates.map((coords) => ({
    type: "Feature",
    properties: {},
    geometry: { type: "Polygon", coordinates: coords },
  }));
}

export function splitPolygonByLine(
  polyFeature: GeoJSON.Feature<GeoJSON.Polygon>,
  cutLine: GeoJSON.Feature<GeoJSON.LineString>,
): GeoJSON.Feature<GeoJSON.Polygon>[] | null {
  const boundary = polygonToLine(polyFeature);
  const boundaryFeatures = boundary.type === "FeatureCollection" ? boundary.features : [boundary];
  const hits = boundaryFeatures.flatMap((ring) => {
    const result = lineIntersect(ring, cutLine);
    return result.features;
  });

  if (hits.length < 2) return null;

  const knife = buffer(cutLine, 0.0000008, { units: "degrees" });
  if (!knife) return null;

  const carved = difference(featureCollection([polyFeature, knife]));
  if (!carved?.geometry) return null;

  const pieces = asPolygons(carved.geometry);
  return pieces.length >= 2 ? pieces.slice(0, 2) : null;
}

export function extendCutLineAcrossPolygon(
  cutLine: GeoJSON.Feature<GeoJSON.LineString>,
): GeoJSON.Feature<GeoJSON.LineString> {
  const coords = cutLine.geometry.coordinates;
  if (coords.length < 2) return cutLine;

  const [start, end] = [coords[0], coords[coords.length - 1]];
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const scale = 4;
  return lineString([
    [start[0] - dx * scale, start[1] - dy * scale],
    [end[0] + dx * scale, end[1] + dy * scale],
  ]);
}

export function deriveSplitUlpins(parentUlpin: string): [string, string] {
  const base = parentUlpin.replace(/\D/g, "").padEnd(16, "0").slice(0, 16);
  const prefix = base.slice(0, -2);
  const suffix = Number(base.slice(-2));
  const first = `${prefix}${String(suffix + 1).padStart(2, "0")}`;
  const second = `${prefix}${String(suffix + 2).padStart(2, "0")}`;
  return [first, second];
}
