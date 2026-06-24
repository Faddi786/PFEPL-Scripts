import cadastralOsmRaw from "./cadastralOsm.json";

export type RegionKey = "puducherry" | "karaikal" | "mahe" | "yanam";

export type RegionConfig = {
  key: RegionKey;
  code: string;
  label: string;
  center: [number, number];
  zoom: number;
  villages: string[];
  taluks: string[];
  ulpinPrefix: string;
  layout?: {
    widthM: number;
    heightM: number;
    blocksX: number;
    blocksY: number;
    roadM: number;
  };
};

export type LayerConfig = {
  id: string;
  label: string;
  visible: boolean;
  opacity?: number;
};

export type LayerGroup = {
  id: string;
  label: string;
  layers: LayerConfig[];
};

export type ParcelRecord = {
  id: string;
  surveyNo: string;
  subDiv: string;
  ulpin: string;
  village: string;
  taluk: string;
  ward: string;
  region: string;
  areaSqM: number;
  owner: string;
  ownerMasked: string;
  status: string;
  classification: string;
  landUse: string;
  encumbrance: string;
  fmbSheet: string;
  varianceBand: "green" | "amber" | "red";
  variancePct: number;
  holdingType: string;
  pattaNo: string;
  deedNo: string;
  registeredOn: string;
  lastSurvey: string;
  taxDue: string;
  mutationRef: string;
  soilType: string;
  roadAccess: string;
  plotFrontageM: number;
  plotDepthM: number;
  source: string;
  osmTag: string;
};

export const PARCEL_DISPLAY_FIELDS: Array<{ key: keyof ParcelRecord; label: string }> = [
  { key: "surveyNo", label: "Survey No" },
  { key: "subDiv", label: "Sub-division" },
  { key: "ulpin", label: "ULPIN" },
  { key: "pattaNo", label: "Patta No" },
  { key: "deedNo", label: "Deed No" },
  { key: "village", label: "Village" },
  { key: "taluk", label: "Taluk" },
  { key: "ward", label: "Ward" },
  { key: "classification", label: "Classification" },
  { key: "landUse", label: "Land use" },
  { key: "holdingType", label: "Holding type" },
  { key: "areaSqM", label: "Area (sq.m)" },
  { key: "plotFrontageM", label: "Frontage (m)" },
  { key: "plotDepthM", label: "Depth (m)" },
  { key: "owner", label: "Owner" },
  { key: "ownerMasked", label: "Owner (masked)" },
  { key: "status", label: "Status" },
  { key: "mutationRef", label: "Mutation ref" },
  { key: "encumbrance", label: "Encumbrance" },
  { key: "fmbSheet", label: "FMB sheet" },
  { key: "varianceBand", label: "Variance band" },
  { key: "variancePct", label: "Variance %" },
  { key: "registeredOn", label: "Registered on" },
  { key: "lastSurvey", label: "Last survey" },
  { key: "taxDue", label: "Tax due" },
  { key: "soilType", label: "Soil type" },
  { key: "roadAccess", label: "Road access" },
  { key: "source", label: "Data source" },
  { key: "osmTag", label: "OSM tag" },
];

type Feature = GeoJSON.Feature<GeoJSON.Geometry, Record<string, any>>;
type FeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, Record<string, any>>;

type OsmCadastralBundle = { features: Feature[]; attrs: Record<string, Record<string, unknown>> };
const CADASTRAL_OSM = cadastralOsmRaw as unknown as Record<RegionKey, OsmCadastralBundle>;

const REGION_CONFIGS: RegionConfig[] = [
  {
    key: "puducherry",
    code: "PY",
    label: "Puducherry",
    center: [79.8083, 11.9375],
    zoom: 15,
    villages: ["Kurumbapet", "Muthialpet", "Ariyankuppam", "Lawspet", "Reddiarpalayam"],
    taluks: ["Oulgaret", "Villianur"],
    ulpinPrefix: "3411",
    layout: { widthM: 4200, heightM: 3600, blocksX: 3, blocksY: 2, roadM: 16 },
  },
  {
    key: "karaikal",
    code: "KR",
    label: "Karaikal",
    center: [79.8372, 10.9254],
    zoom: 15,
    villages: ["Nedungadu", "Kottucherry", "Tirumalairayanpattinam", "Neravy", "Varichikudy"],
    taluks: ["Karaikal", "Thirunallar"],
    ulpinPrefix: "3412",
    layout: { widthM: 4000, heightM: 3800, blocksX: 3, blocksY: 2, roadM: 14 },
  },
  {
    key: "mahe",
    code: "MH",
    label: "Mahe",
    center: [75.5503, 11.7012],
    zoom: 16,
    villages: ["Mahe Town", "Chalakkara", "Palloor", "Pandakkal"],
    taluks: ["Mahe", "Palloor"],
    ulpinPrefix: "3413",
    layout: { widthM: 2600, heightM: 2300, blocksX: 2, blocksY: 2, roadM: 12 },
  },
  {
    key: "yanam",
    code: "YN",
    label: "Yanam",
    center: [82.2155, 16.7351],
    zoom: 16,
    villages: ["Mettakur", "Kanakalapeta", "Adavipolam", "Jambavanpet"],
    taluks: ["Yanam", "Kanakalapeta"],
    ulpinPrefix: "3414",
    layout: { widthM: 3000, heightM: 2600, blocksX: 2, blocksY: 3, roadM: 12 },
  },
];

const LAYER_GROUPS: LayerGroup[] = [
  {
    id: "basemap",
    label: "Basemap",
    layers: [
      { id: "basemap-carto", label: "Carto Positron", visible: true },
      { id: "basemap-osm", label: "OpenStreetMap", visible: false },
      { id: "basemap-imagery", label: "Esri Imagery", visible: false },
    ],
  },
  {
    id: "imagery",
    label: "Imagery",
    layers: [{ id: "ortho", label: "Ortho Reference", visible: true, opacity: 0.45 }],
  },
  {
    id: "cadastral",
    label: "Cadastral",
    layers: [
      { id: "parcels", label: "Parcel Boundaries", visible: true, opacity: 0.9 },
      { id: "fmb", label: "FMB Sheet Outlines", visible: true, opacity: 0.75 },
    ],
  },
  {
    id: "admin",
    label: "Administrative",
    layers: [
      { id: "region", label: "Region", visible: true, opacity: 0.4 },
      { id: "taluk", label: "Taluk", visible: true, opacity: 0.45 },
      { id: "village", label: "Village", visible: true, opacity: 0.45 },
      { id: "ward", label: "Ward", visible: true, opacity: 0.4 },
    ],
  },
  {
    id: "field",
    label: "Field & Analytics",
    layers: [
      { id: "variance", label: "Variance Bands", visible: true, opacity: 0.45 },
      { id: "dgps", label: "DGPS / GNSS Points", visible: true, opacity: 1 },
      { id: "collabland", label: "CollabLand Reference", visible: true, opacity: 0.85 },
    ],
  },
];

function metersToLatDeg(meters: number) {
  return meters / 111_320;
}

function metersToLonDeg(meters: number, latitude: number) {
  const scale = Math.max(0.2, Math.abs(Math.cos((latitude * Math.PI) / 180)));
  return meters / (111_320 * scale);
}

function toPolygon(coords: [number, number][], properties: Record<string, any> = {}): Feature {
  return {
    type: "Feature",
    properties,
    geometry: { type: "Polygon", coordinates: [coords] },
  };
}

function toPoint(coord: [number, number], properties: Record<string, any> = {}): Feature {
  return {
    type: "Feature",
    properties,
    geometry: { type: "Point", coordinates: coord },
  };
}

function toLine(coords: [number, number][], properties: Record<string, any> = {}): Feature {
  return {
    type: "Feature",
    properties,
    geometry: { type: "LineString", coordinates: coords },
  };
}

function bboxFromParcels(parcelFeatures: Feature[]): [number, number, number, number] {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  parcelFeatures.forEach((feature) => {
    const ring = (feature.geometry as GeoJSON.Polygon).coordinates[0];
    ring.forEach(([x, y]) => {
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    });
  });
  return [minX, minY, maxX, maxY];
}

function bboxPolygon(minX: number, minY: number, maxX: number, maxY: number): [number, number][] {
  return [
    [minX, minY],
    [maxX, minY],
    [maxX, maxY],
    [minX, maxY],
    [minX, minY],
  ];
}

function pickByIndex<T>(list: T[], index: number) {
  if (!list.length) return list[0];
  return list[index % list.length];
}

function partitionWeights(total: number, parts: number, rng: () => number, minFrac: number) {
  if (parts <= 0) return [0, total];
  const weights: number[] = [];
  let sum = 0;
  for (let i = 0; i < parts; i += 1) {
    const weight = minFrac + rng() * (1 - minFrac);
    weights.push(weight);
    sum += weight;
  }
  const positions = [0];
  let acc = 0;
  for (let j = 0; j < parts; j += 1) {
    acc += (weights[j] / sum) * total;
    positions.push(acc);
  }
  positions[positions.length - 1] = total;
  return positions;
}

function jitteredPartitions(baseOffsets: number[], rng: () => number, jitterMax: number, minGap: number) {
  const out = baseOffsets.slice();
  for (let i = 1; i < out.length - 1; i += 1) {
    out[i] += (rng() - 0.5) * jitterMax;
  }
  for (let k = 1; k < out.length; k += 1) {
    if (out[k] <= out[k - 1] + minGap) out[k] = out[k - 1] + minGap;
  }
  out[0] = baseOffsets[0];
  out[out.length - 1] = baseOffsets[baseOffsets.length - 1];
  return out;
}

function localRingToGeo(ringLocal: [number, number][], config: RegionConfig): [number, number][] {
  return ringLocal.map(([x, y]) => [
    config.center[0] + metersToLonDeg(x, config.center[1]),
    config.center[1] + metersToLatDeg(y),
  ]);
}

function quadAreaSqM(sw: [number, number], se: [number, number], ne: [number, number], nw: [number, number]) {
  const ring = [sw, se, ne, nw, sw];
  let area = 0;
  for (let i = 0; i < 4; i += 1) {
    area += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
  }
  return Math.abs(area) / 2;
}

function makeSurveyNo(blockNo: number, parcelInBlock: number, rng: () => number) {
  const main = blockNo * 23 + parcelInBlock;
  if (rng() > 0.68) return `${main}/${1 + (parcelInBlock % 5)}`;
  if (rng() > 0.9) return `${main}/${1 + (parcelInBlock % 3)}${String.fromCharCode(65 + (parcelInBlock % 3))}`;
  return String(main);
}

function generateCadastralParcels(config: RegionConfig, rng: () => number, owners: string[]) {
  const layout = config.layout ?? {
    widthM: 3600,
    heightM: 3000,
    blocksX: 3,
    blocksY: 2,
    roadM: 14,
  };
  const { widthM: totalW, heightM: totalH, blocksX, blocksY, roadM: road } = layout;
  const blockCellW = (totalW - road * (blocksX - 1)) / blocksX;
  const blockCellH = (totalH - road * (blocksY - 1)) / blocksY;
  const originWest = -totalW / 2;
  const originSouth = -totalH / 2;

  const parcelFeatures: Feature[] = [];
  const parcelAttrs: Record<string, ParcelRecord> = {};
  let parcelIndex = 1;

  for (let by = 0; by < blocksY; by += 1) {
    for (let bx = 0; bx < blocksX; bx += 1) {
      const blockWest = originWest + bx * (blockCellW + road);
      const blockSouth = originSouth + by * (blockCellH + road);
      const blockNo = by * blocksX + bx + 1;
      const rows = 4 + Math.floor(rng() * 8);
      const yOffsets = partitionWeights(blockCellH, rows, rng, 0.03);
      const yLines = yOffsets.map((value) => blockSouth + value);
      let parcelInBlock = 0;

      for (let row = 0; row < rows; row += 1) {
        const colsThisRow = 5 + Math.floor(rng() * 9);
        const xBottom = jitteredPartitions(
          partitionWeights(blockCellW, colsThisRow, rng, 0.025).map((value) => blockWest + value),
          rng,
          blockCellW * 0.022,
          2.5,
        );
        const xTop = jitteredPartitions(
          partitionWeights(blockCellW, colsThisRow, rng, 0.025).map((value) => blockWest + value),
          rng,
          blockCellW * 0.028,
          2.5,
        );
        const y0 = yLines[row];
        const y1 = yLines[row + 1];

        for (let col = 0; col < colsThisRow; col += 1) {
          if (rng() < 0.02) continue;

          const sw: [number, number] = [xBottom[col], y0];
          const se: [number, number] = [xBottom[col + 1], y0];
          const ne: [number, number] = [xTop[col + 1], y1];
          const nw: [number, number] = [xTop[col], y1];
          const areaSqM = Math.round(quadAreaSqM(sw, se, ne, nw));
          if (areaSqM < 20) continue;

          parcelInBlock += 1;
          const ring = localRingToGeo([sw, se, ne, nw, sw], config);
          const surveyNo = makeSurveyNo(blockNo, parcelInBlock, rng);
          const subDiv = surveyNo.includes("/") ? surveyNo.split("/")[1] : String((col % 4) + 1);
          const id = `${config.code}-P-${String(parcelIndex).padStart(3, "0")}`;
          const ulpin = `${config.ulpinPrefix}${String(parcelIndex).padStart(10, "0")}`;
          const village = pickByIndex(config.villages, parcelIndex - 1);
          const taluk = pickByIndex(config.taluks, parcelIndex - 1);
          const ward = `Ward ${((parcelIndex - 1) % 12) + 1}`;
          const owner = pickByIndex(owners, parcelIndex - 1);
          const ownerMasked = `${owner.charAt(0)}********`;
          const statusRoll = rng();
          const status = statusRoll < 0.82 ? "active" : statusRoll < 0.92 ? "mutation_pending" : "disputed";

          const attrs = enrichParcelRecord(
            {
              id,
              surveyNo,
              subDiv,
              ulpin,
              village,
              taluk,
              ward,
              region: config.label,
              areaSqM,
              owner,
              ownerMasked,
              status,
              classification: rng() > 0.58 ? "Punjai" : "Nanjai",
              landUse: rng() > 0.52 ? "Residential" : "Agriculture",
              encumbrance: rng() > 0.86 ? "Bank lien (sample)" : "None",
              fmbSheet: `${config.code}-FMB-${String(blockNo).padStart(2, "0")}`,
            },
            parcelIndex,
            config,
            rng,
          );

          parcelFeatures.push(toPolygon(ring, attrs));
          parcelAttrs[id] = attrs;
          parcelIndex += 1;
        }
      }
    }
  }

  return { parcelFeatures, parcelAttrs };
}

function enrichParcelRecord(
  base: Record<string, any>,
  parcelIndex: number,
  config: RegionConfig,
  rng: () => number,
): ParcelRecord {
  const variancePct = Number((rng() * 4.8).toFixed(2));
  const varianceBand: ParcelRecord["varianceBand"] =
    variancePct > 3.6 ? "red" : variancePct > 2.2 ? "amber" : "green";
  const statusRoll = rng();
  const status =
    base.status ?? (statusRoll < 0.82 ? "active" : statusRoll < 0.92 ? "mutation_pending" : "disputed");
  const classification = base.classification ?? (rng() > 0.58 ? "Punjai" : "Nanjai");

  return {
    id: String(base.id),
    surveyNo: String(base.surveyNo),
    subDiv: String(base.subDiv ?? (parcelIndex % 4) + 1),
    ulpin: String(base.ulpin),
    village: String(base.village),
    taluk: String(base.taluk),
    ward: String(base.ward),
    region: String(base.region ?? config.label),
    areaSqM: Number(base.areaSqM),
    owner: String(base.owner),
    ownerMasked: String(base.ownerMasked ?? `${String(base.owner).charAt(0)}********`),
    status: String(status),
    classification,
    landUse: String(base.landUse ?? (rng() > 0.52 ? "Residential" : "Agriculture")),
    encumbrance: String(base.encumbrance ?? (rng() > 0.86 ? "Bank lien (sample)" : "None")),
    fmbSheet: String(base.fmbSheet ?? `${config.code}-FMB-${String(1 + (parcelIndex % 12)).padStart(2, "0")}`),
    varianceBand,
    variancePct,
    holdingType: classification === "Nanjai" ? "Wet" : "Dry",
    pattaNo: `PT-${config.code}-${String(parcelIndex).padStart(5, "0")}`,
    deedNo: `${config.code}/DEED/${12000 + parcelIndex}`,
    registeredOn: `201${2 + (parcelIndex % 8)}-${String(1 + (parcelIndex % 12)).padStart(2, "0")}-${String(1 + (parcelIndex % 28)).padStart(2, "0")}`,
    lastSurvey: `Revenue Survey ${2010 + (parcelIndex % 12)}`,
    taxDue: status === "disputed" ? "Pending verification" : "Nil",
    mutationRef:
      status === "mutation_pending"
        ? `${config.code}-MUT-2026-${String(parcelIndex).padStart(4, "0")}`
        : "—",
    soilType: parcelIndex % 3 === 0 ? "Sandy loam" : parcelIndex % 3 === 1 ? "Clay loam" : "Alluvial",
    roadAccess: parcelIndex % 2 === 0 ? "Tar road frontage" : "Interior lane",
    plotFrontageM: Math.round(6 + rng() * 28),
    plotDepthM: Math.round(8 + rng() * 42),
    source: String(base.source ?? "OpenStreetMap/Carto Positron footprint"),
    osmTag: String(base.osmTag ?? "building"),
  };
}

const OWNER_POOL = [
  "S. Ravi",
  "M. Lakshmi",
  "P. Kannan",
  "R. Salma",
  "A. Joseph",
  "K. Nirmala",
  "T. Rahim",
  "V. Anandhi",
  "D. Prakash",
  "G. Mariam",
  "N. Suresh",
  "F. Ashok",
];

function loadCadastralParcels(config: RegionConfig): { parcels: Feature[]; parcelAttrs: Record<string, ParcelRecord> } {
  const osm = CADASTRAL_OSM[config.key];
  if (osm?.features?.length) {
    const parcelAttrs: Record<string, ParcelRecord> = {};
    const parcels = osm.features.map((feature, idx) => {
      const rng = seeded(`${config.key}-${feature.properties.id}`);
      const enriched = enrichParcelRecord(feature.properties, idx + 1, config, rng);
      parcelAttrs[enriched.id] = enriched;
      return { ...feature, properties: enriched };
    });
    return { parcels, parcelAttrs };
  }

  const rng = seeded(`${config.key}-cadastral`);
  const generated = generateCadastralParcels(config, rng, OWNER_POOL);
  return { parcels: generated.parcelFeatures, parcelAttrs: generated.parcelAttrs };
}

function seeded(seedText: string) {
  let seed = 0;
  for (let i = 0; i < seedText.length; i += 1) {
    seed = (seed * 31 + seedText.charCodeAt(i)) >>> 0;
  }
  return () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
}

function computeCadastralView(parcels: Feature[]): { center: [number, number]; zoom: number } {
  const [minX, minY, maxX, maxY] = bboxFromParcels(parcels);
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const widthM = (maxX - minX) * 111_320 * Math.cos((cy * Math.PI) / 180);
  const heightM = (maxY - minY) * 111_320;
  const aspect = widthM / Math.max(heightM, 1);
  const spanM =
    aspect > 2.5 ? Math.max(widthM * 0.58, heightM * 3.2) : Math.max(widthM * 0.72, heightM * 0.88);
  const metersPerPixel = spanM / 900;
  const zoom = Math.log2((156_543.03392 * Math.cos((cy * Math.PI) / 180)) / metersPerPixel);
  return {
    center: [cx, cy],
    zoom: Math.min(Math.max(Number((zoom + 1.45).toFixed(2)), 16), 19.25),
  };
}

export type RegionDataset = {
  center: [number, number];
  zoom: number;
  cadastralView: { center: [number, number]; zoom: number };
  parcelAttrs: Record<string, ParcelRecord>;
  parcels: ParcelRecord[];
  geojson: Record<string, FeatureCollection>;
  controlPoints: Array<{ id: string; source: string; status: string; rmse: number; lat: number; lng: number }>;
};

function generateRegionDataset(config: RegionConfig): RegionDataset {
  const { parcels, parcelAttrs } = loadCadastralParcels(config);

  const [minX, minY, maxX, maxY] = bboxFromParcels(parcels);
  const midX = (minX + maxX) / 2;
  const midY = (minY + maxY) / 2;
  const width = maxX - minX;
  const height = maxY - minY;

  const regionPoly = toPolygon(
    bboxPolygon(minX - width * 0.04, minY - height * 0.04, maxX + width * 0.04, maxY + height * 0.04),
    { name: `${config.label} Region`, level: "region" },
  );

  const talukPolys = config.taluks.map((name, idx) => {
    const tMinX = idx % 2 === 0 ? minX : midX;
    const tMaxX = idx % 2 === 0 ? midX : maxX;
    return toPolygon(bboxPolygon(tMinX, minY, tMaxX, maxY), { name, level: "taluk" });
  });

  const villageFeatures = config.villages.map((name, idx) => {
    const vBand = idx / config.villages.length;
    const vMinY = minY + height * vBand;
    const vMaxY = minY + height * ((idx + 1) / config.villages.length);
    return toPolygon(bboxPolygon(minX, vMinY, maxX, vMaxY), { name, level: "village" });
  });

  const wardPolys = [
    toPolygon(bboxPolygon(minX, minY, midX, midY), { name: "Ward 1", level: "ward" }),
    toPolygon(bboxPolygon(midX, minY, maxX, midY), { name: "Ward 2", level: "ward" }),
    toPolygon(bboxPolygon(minX, midY, midX, maxY), { name: "Ward 3", level: "ward" }),
    toPolygon(bboxPolygon(midX, midY, maxX, maxY), { name: "Ward 4", level: "ward" }),
  ];

  const fmbFeatures = Array.from({ length: 4 }).map((_, fm) => {
    const sx = minX + (width * fm) / 4;
    const ex = minX + (width * (fm + 1)) / 4;
    return toPolygon(bboxPolygon(sx, minY, ex, maxY), {
      sheet: `${config.code}-FMB-${String(fm + 1).padStart(2, "0")}`,
      village: pickByIndex(config.villages, fm),
    });
  });

  const DGPS_POINT_COUNT = 50;
  const dgpsCols = 10;
  const dgpsRows = Math.ceil(DGPS_POINT_COUNT / dgpsCols);
  const dgps = Array.from({ length: DGPS_POINT_COUNT }).map((_, g) => {
    const row = Math.floor(g / dgpsCols);
    const col = g % dgpsCols;
    const jitterLon = (((g * 17 + 3) % 100) / 100 - 0.5) * width * 0.018;
    const jitterLat = (((g * 23 + 7) % 100) / 100 - 0.5) * height * 0.018;
    const lon = minX + (width * (col + 0.5)) / dgpsCols + jitterLon;
    const lat = minY + (height * (row + 0.5)) / dgpsRows + jitterLat;
    const sources = ["DGPS", "GNSS RTK", "NTRIP"] as const;
    return toPoint([lon, lat], {
      id: `${config.code}-GCP-${String(g + 1).padStart(3, "0")}`,
      source: sources[g % sources.length],
      rmse: Number((0.04 + (g % 14) * 0.016).toFixed(2)),
    });
  });

  const variance = parcels.map((feature: Feature) =>
    toPolygon((feature.geometry as GeoJSON.Polygon).coordinates[0] as [number, number][], {
      band: feature.properties.varianceBand,
      pct: feature.properties.variancePct,
      surveyNo: feature.properties.surveyNo,
      parcelId: feature.properties.id,
    }),
  );

  const collabLine = toLine(
    [
      [minX, minY],
      [midX, midY],
      [maxX, maxY],
    ],
    { ref: `CollabLand ${config.label} sample baseline` },
  );

  const orthoPoly = toPolygon(
    bboxPolygon(minX - width * 0.02, minY - height * 0.02, maxX + width * 0.02, maxY + height * 0.02),
    { name: `${config.label} Ortho Reference 2026` },
  );

  const cadastralView = computeCadastralView(parcels);

  return {
    center: cadastralView.center,
    zoom: cadastralView.zoom,
    cadastralView,
    parcelAttrs,
    parcels: Object.values(parcelAttrs),
    geojson: {
      region: { type: "FeatureCollection", features: [regionPoly] },
      taluk: { type: "FeatureCollection", features: talukPolys },
      village: { type: "FeatureCollection", features: villageFeatures },
      ward: { type: "FeatureCollection", features: wardPolys },
      fmb: { type: "FeatureCollection", features: fmbFeatures },
      parcels: { type: "FeatureCollection", features: parcels },
      variance: { type: "FeatureCollection", features: variance },
      dgps: { type: "FeatureCollection", features: dgps },
      collabland: { type: "FeatureCollection", features: [collabLine] },
      ortho: { type: "FeatureCollection", features: [orthoPoly] },
    },
    controlPoints: dgps.map((feature) => ({
      id: String(feature.properties.id),
      source: String(feature.properties.source),
      status: "accepted",
      rmse: Number(feature.properties.rmse),
      lat: (feature.geometry as GeoJSON.Point).coordinates[1],
      lng: (feature.geometry as GeoJSON.Point).coordinates[0],
    })),
  };
}

const DATASETS: Record<RegionKey, RegionDataset> = Object.fromEntries(
  REGION_CONFIGS.map((region) => [region.key, generateRegionDataset(region)]),
) as Record<RegionKey, RegionDataset>;

export function getRegions() {
  return REGION_CONFIGS.map((region) => ({
    key: region.key,
    code: region.code,
    label: region.label,
    center: region.center,
    zoom: region.zoom,
  }));
}

export function getLayerGroups() {
  return LAYER_GROUPS;
}

export function getRegionDataset(regionKey: RegionKey) {
  return DATASETS[regionKey] ?? DATASETS.puducherry;
}
