import { getRegionDataset, type ParcelRecord, type RegionKey } from "./mockData";
import { NIL_AI_EXPORTS, type NilAiAttachment } from "../lib/nilAiExport";

export type { NilAiAttachment };

export type NilAiResult = {
  reply: string;
  parcelIds: string[];
  attachments?: NilAiAttachment[];
};

export type NilAiSuggestion = {
  id: string;
  label: string;
  prompt: string;
};

export const NIL_AI_SUGGESTIONS: NilAiSuggestion[] = [
  {
    id: "mutation-kurumbapet",
    label: "Mutation-pending · Kurumbapet",
    prompt: "Locate mutation-pending parcels in the Kurumbapet corridor",
  },
  {
    id: "variance-ariyankuppam",
    label: "Variance bands · Ariyankuppam",
    prompt: "Flag amber and red variance bands on agricultural parcels in the Ariyankuppam block",
  },
  {
    id: "analysis-report",
    label: "Download analysis report",
    prompt: "Generate a cadastral data analysis report with parcel maps and attribute tables in PDF format",
  },
];

type ParcelFeature = {
  properties: ParcelRecord;
  centroid: [number, number];
};

function polygonCentroid(coords: GeoJSON.Polygon["coordinates"]): [number, number] {
  const ring = coords[0];
  let lng = 0;
  let lat = 0;
  const count = ring.length - 1;
  for (let i = 0; i < count; i += 1) {
    lng += ring[i][0];
    lat += ring[i][1];
  }
  return [lng / count, lat / count];
}

export function getParcelFeatures(regionKey: RegionKey = "puducherry"): ParcelFeature[] {
  const dataset = getRegionDataset(regionKey);
  return dataset.geojson.parcels.features.map((feature) => ({
    properties: feature.properties as ParcelRecord,
    centroid: polygonCentroid((feature.geometry as GeoJSON.Polygon).coordinates),
  }));
}

export function getParcelsFromDataset(regionKey: RegionKey = "puducherry"): ParcelRecord[] {
  return getParcelFeatures(regionKey).map((item) => item.properties);
}

function percentile(values: number[], ratio: number) {
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.floor(sorted.length * ratio));
  return sorted[index];
}

function pickFromZone(
  features: ParcelFeature[],
  zone: "north-east" | "south-west",
  filter: (parcel: ParcelRecord) => boolean,
  limit = 5,
): ParcelRecord[] {
  const lngs = features.map((item) => item.centroid[0]);
  const lats = features.map((item) => item.centroid[1]);
  const lngHigh = percentile(lngs, 0.72);
  const lngLow = percentile(lngs, 0.28);
  const latHigh = percentile(lats, 0.72);
  const latLow = percentile(lats, 0.28);

  const matched = features.filter((item) => {
    const [lng, lat] = item.centroid;
    const inZone =
      zone === "north-east" ? lng >= lngHigh && lat >= latHigh : lng <= lngLow && lat <= latLow;
    return inZone && filter(item.properties);
  });

  if (matched.length < limit) {
    const fallback = features
      .filter((item) => filter(item.properties))
      .sort((a, b) => {
        const scoreA =
          zone === "north-east" ? a.centroid[0] + a.centroid[1] : -(a.centroid[0] + a.centroid[1]);
        const scoreB =
          zone === "north-east" ? b.centroid[0] + b.centroid[1] : -(b.centroid[0] + b.centroid[1]);
        return scoreB - scoreA;
      });
    return fallback.slice(0, limit).map((item) => item.properties);
  }

  return matched.slice(0, limit).map((item) => item.properties);
}

function formatParcelReply(parcels: ParcelRecord[], intro: string, outro: string): NilAiResult {
  const lines = parcels.map(
    (parcel) =>
      `- Survey **${parcel.surveyNo}** - ${parcel.village}, ${parcel.ward}, ${parcel.landUse}, ${parcel.areaSqM.toLocaleString()} sq m`,
  );

  return {
    reply: [intro, "", ...lines, "", outro].join("\n"),
    parcelIds: parcels.map((parcel) => parcel.id),
  };
}

function reportAttachments(): NilAiAttachment[] {
  return [
    {
      id: "pdf",
      title: NIL_AI_EXPORTS.pdf.title,
      subtitle: NIL_AI_EXPORTS.pdf.subtitle,
      url: NIL_AI_EXPORTS.pdf.url,
      filename: NIL_AI_EXPORTS.pdf.filename,
      kind: "pdf",
    },
    {
      id: "xlsx",
      title: NIL_AI_EXPORTS.xlsx.title,
      subtitle: NIL_AI_EXPORTS.xlsx.subtitle,
      url: NIL_AI_EXPORTS.xlsx.url,
      filename: NIL_AI_EXPORTS.xlsx.filename,
      kind: "xlsx",
    },
  ];
}

type ScenarioId = "mutation-ne" | "variance-sw" | "report" | "fallback";

function detectScenario(text: string): ScenarioId {
  if (/report|pdf|analysis|download|export|generate|dashboard|attribute table|spreadsheet|excel/.test(text)) {
    return "report";
  }
  if (/mutation|pending|transfer|kurumbapet|corridor|north-east|northeast/.test(text)) {
    return "mutation-ne";
  }
  if (/variance|anomal|amber|red|agricultur|ariyankuppam|lawspet|south-west|southwest/.test(text)) {
    return "variance-sw";
  }
  return "fallback";
}

export function resolveNilAiPrompt(prompt: string, features: ParcelFeature[]): NilAiResult {
  const text = prompt.toLowerCase().trim();
  if (!text) {
    return {
      reply: [
        "Ask NIL-AI to query the map or generate a cadastral analysis report.",
        "",
        "Examples: mutation-pending parcels in Kurumbapet, variance bands in Ariyankuppam, or download analysis report.",
      ].join("\n"),
      parcelIds: [],
    };
  }

  const scenario = detectScenario(text);

  if (scenario === "report") {
    return {
      reply: [
        "I've compiled the **cadastral data analysis report** from the current map scope.",
        "",
        "The PDF includes parcel geometries over a satellite basemap on the left, a structured attribute table on the right, and DoSLR header/footer blocks with run metadata and variance summary.",
        "",
        "Open the files below in a new tab — PDF for presentation and spreadsheet for desk review.",
      ].join("\n"),
      parcelIds: [],
      attachments: reportAttachments(),
    };
  }

  if (scenario === "mutation-ne") {
    const parcels = pickFromZone(
      features,
      "north-east",
      (parcel) =>
        parcel.village.toLowerCase().includes("kurumbapet") ||
        parcel.status.toLowerCase().includes("mutation") ||
        parcel.status.toLowerCase().includes("pending") ||
        Boolean(parcel.mutationRef),
      5,
    );
    return formatParcelReply(
      parcels,
      `**${parcels.length} mutation-pending parcel${parcels.length === 1 ? "" : "s"}** in the **Kurumbapet corridor** (north-east cluster).`,
      "Panning to the north-east sector. RoR ledger cross-check complete — highlighted boundaries are ready for review.",
    );
  }

  if (scenario === "variance-sw") {
    const parcels = pickFromZone(
      features,
      "south-west",
      (parcel) =>
        (parcel.landUse === "Agriculture" ||
          parcel.village.toLowerCase().includes("ariyankuppam") ||
          parcel.village.toLowerCase().includes("lawspet")) &&
        (parcel.varianceBand === "amber" || parcel.varianceBand === "red"),
      5,
    );
    return formatParcelReply(
      parcels,
      `**${parcels.length} elevated-variance agricultural parcel${parcels.length === 1 ? "" : "s"}** in the **Ariyankuppam / Lawspet block** (south-west cluster).`,
      "Panning to the south-west sector. Amber and red ST_Area vs RoR deviations are flagged for field reconciliation.",
    );
  }

  return {
    reply: [
      "I'm **NIL-AI**, your cadastral intelligence assistant for DoSLR.",
      "",
      "Try one of these actions:",
      ...NIL_AI_SUGGESTIONS.map((item) => `- *${item.prompt}*`),
    ].join("\n"),
    parcelIds: [],
  };
}
