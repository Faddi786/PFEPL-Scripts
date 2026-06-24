import { getRegionDataset } from "../../data/mockData";

export type AnomalyPipelinePhase =
  | "idle"
  | "satellite"
  | "digitized"
  | "comparing"
  | "bands"
  | "boundary"
  | "complete";

export type VarianceBand = "green" | "amber" | "red";

export const VARIANCE_BAND_COLORS: Record<
  VarianceBand,
  { fill: string; stroke: string; label: string; threshold: string }
> = {
  green: { fill: "rgba(34,197,94,0.55)", stroke: "#15803d", label: "Green", threshold: "≤ 1% variance" },
  amber: { fill: "rgba(245,158,11,0.55)", stroke: "#b45309", label: "Amber", threshold: "1–5% variance" },
  red: { fill: "rgba(239,68,68,0.55)", stroke: "#b91c1c", label: "Red", threshold: "> 5% variance" },
};

export type RecordMapCheck = {
  id: string;
  label: string;
  detail: string;
  flaggedParcelIndices: number[];
};

export const RECORD_MAP_CHECKS: RecordMapCheck[] = [
  { id: "missing-ror", label: "Missing RoR", detail: "All scoped parcels have linked RoR records", flaggedParcelIndices: [] },
  {
    id: "missing-geometry",
    label: "Missing geometry",
    detail: "4 parcels flagged — geometry null in cadastral store",
    flaggedParcelIndices: [2, 7, 18, 31],
  },
  { id: "duplicate-geom", label: "Duplicate geom", detail: "No overlapping parcel footprints detected", flaggedParcelIndices: [] },
  {
    id: "ulpin-conflict",
    label: "ULPIN conflict",
    detail: "3 duplicate ULPIN candidates in Ward 2 batch",
    flaggedParcelIndices: [5, 22, 41],
  },
  {
    id: "classification-mismatch",
    label: "Classification + ownership mismatch",
    detail: "8 parcels: land-use class differs from RoR ownership class",
    flaggedParcelIndices: [1, 4, 9, 14, 23, 28, 36, 44],
  },
];

const CLUSTER_SIZE = 50;
const NEIGHBOR_RADIUS_DEG = 0.00014;

function polygonCentroid(feature: GeoJSON.Feature<GeoJSON.Polygon>): [number, number] {
  const ring = feature.geometry.coordinates[0];
  let lng = 0;
  let lat = 0;
  const count = ring.length - 1;
  for (let i = 0; i < count; i += 1) {
    lng += ring[i][0];
    lat += ring[i][1];
  }
  return [lng / count, lat / count];
}

function centroidDistance(a: [number, number], b: [number, number]) {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function findDenseCluster(features: GeoJSON.Feature<GeoJSON.Polygon>[]) {
  const items = features.map((feature) => ({
    feature,
    centroid: polygonCentroid(feature),
    surveyNo: String(feature.properties?.surveyNo ?? ""),
  }));

  const preferred = items.find((item) => item.surveyNo === "42" || item.surveyNo.includes("52/"));
  let seed = preferred ?? items[0];
  let bestNeighborCount = -1;

  for (const item of items) {
    const neighbors = items.filter(
      (other) => other !== item && centroidDistance(other.centroid, item.centroid) <= NEIGHBOR_RADIUS_DEG,
    ).length;
    if (neighbors > bestNeighborCount) {
      bestNeighborCount = neighbors;
      seed = item;
    }
  }

  const cluster = [seed];
  const remaining = items.filter((item) => item !== seed);

  while (cluster.length < CLUSTER_SIZE && remaining.length > 0) {
    let bestIndex = 0;
    let bestDistance = Number.POSITIVE_INFINITY;

    remaining.forEach((candidate, index) => {
      const nearest = Math.min(...cluster.map((member) => centroidDistance(member.centroid, candidate.centroid)));
      if (nearest < bestDistance) {
        bestDistance = nearest;
        bestIndex = index;
      }
    });

    cluster.push(remaining.splice(bestIndex, 1)[0]);
  }

  return cluster.map((item) => item.feature);
}

function varianceBandForIndex(index: number): VarianceBand {
  if (index % 7 === 0 || index % 11 === 0) return "red";
  if (index % 3 === 0 || index % 5 === 0) return "amber";
  return "green";
}

function variancePctForBand(band: VarianceBand, index: number) {
  const seed = (index * 17 + 3) % 100;
  if (band === "green") return Number((0.4 + (seed % 55) / 100).toFixed(2));
  if (band === "amber") return Number((1.2 + (seed % 35) / 10).toFixed(2));
  return Number((5.5 + (seed % 42) / 10).toFixed(2));
}

export function pickDemoParcels() {
  const dataset = getRegionDataset("puducherry");
  const features = dataset.geojson.parcels.features as GeoJSON.Feature<GeoJSON.Polygon>[];
  const cluster = findDenseCluster(features);

  return cluster.map((feature, index) => {
    const varianceBand = varianceBandForIndex(index);
    return {
      ...feature,
      properties: {
        ...(feature.properties ?? {}),
        varianceBand,
        variancePct: variancePctForBand(varianceBand, index),
        demoDigitizedOffset:
          index % 4 === 0 ? 0.000004 : index % 4 === 1 ? -0.000003 : index % 4 === 2 ? 0.000002 : 0,
        boundaryFlag: varianceBand === "red" || varianceBand === "amber",
      },
    };
  }) as GeoJSON.Feature<GeoJSON.Polygon>[];
}

export function offsetPolygon(
  feature: GeoJSON.Feature<GeoJSON.Polygon>,
  deltaLng: number,
): GeoJSON.Feature<GeoJSON.Polygon> {
  const coords = feature.geometry.coordinates.map((ring) =>
    ring.map(([lng, lat]) => [lng + deltaLng, lat] as [number, number]),
  );
  return {
    ...feature,
    geometry: { type: "Polygon", coordinates: coords },
  };
}
