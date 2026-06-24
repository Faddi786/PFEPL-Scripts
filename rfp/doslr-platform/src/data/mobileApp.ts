import { getRegionDataset, type ParcelRecord } from "./mockData";

export type MobileTab = "home" | "map" | "search" | "capture" | "sync";

export type FieldOfficer = {
  id: string;
  name: string;
  role: string;
  badge: string;
  assignedVillage: string;
  assignedTaluk: string;
  region: string;
};

export type FieldPacket = {
  id: string;
  village: string;
  parcelCount: number;
  status: "assigned" | "downloaded" | "in-progress" | "synced";
  dueDate: string;
  progressPct: number;
};

export type CapturedGnssPoint = {
  id: string;
  label: string;
  lat: number;
  lng: number;
  accuracyM: number;
  source: "bluetooth" | "ntrip" | "file";
  capturedAt: string;
  synced: boolean;
};

export const DEMO_FIELD_OFFICER: FieldOfficer = {
  id: "surveyor.py.1042",
  name: "R. Venkatesh",
  role: "Revenue Surveyor",
  badge: "PY-SRV-1042",
  assignedVillage: "Kurumbapet",
  assignedTaluk: "Oulgaret",
  region: "Puducherry UT",
};

export const FIELD_PACKETS: FieldPacket[] = [
  {
    id: "pkt-kuru-042",
    village: "Kurumbapet",
    parcelCount: 48,
    status: "in-progress",
    dueDate: "18 Jun 2026",
    progressPct: 62,
  },
  {
    id: "pkt-muth-011",
    village: "Muthialpet",
    parcelCount: 32,
    status: "assigned",
    dueDate: "25 Jun 2026",
    progressPct: 0,
  },
];

const dataset = getRegionDataset("puducherry");

export const MOBILE_PARCELS: ParcelRecord[] = dataset.parcels.slice(0, 60);

export function searchMobileParcels(query: string): ParcelRecord[] {
  const q = query.trim().toLowerCase();
  if (!q) return MOBILE_PARCELS.slice(0, 18);
  return MOBILE_PARCELS.filter(
    (p) =>
      p.surveyNo.toLowerCase().includes(q) ||
      p.subDiv.toLowerCase().includes(q) ||
      p.ulpin.toLowerCase().includes(q) ||
      p.village.toLowerCase().includes(q),
  ).slice(0, 12);
}

export function getMobileParcel(id: string): ParcelRecord | undefined {
  return dataset.parcels.find((p) => p.id === id);
}

export const INITIAL_GNSS_POINTS: CapturedGnssPoint[] = [
  {
    id: "gnss-001",
    label: "GCP-KUR-12",
    lat: 11.93742,
    lng: 79.80818,
    accuracyM: 0.08,
    source: "bluetooth",
    capturedAt: "2026-06-10 09:14",
    synced: true,
  },
  {
    id: "gnss-002",
    label: "GCP-KUR-13",
    lat: 11.93788,
    lng: 79.80862,
    accuracyM: 0.11,
    source: "ntrip",
    capturedAt: "2026-06-10 09:22",
    synced: false,
  },
  {
    id: "gnss-003",
    label: "GCP-KUR-14",
    lat: 11.93715,
    lng: 79.80895,
    accuracyM: 0.09,
    source: "bluetooth",
    capturedAt: "2026-06-10 10:05",
    synced: true,
  },
  {
    id: "gnss-004",
    label: "GCP-KUR-15",
    lat: 11.93692,
    lng: 79.80784,
    accuracyM: 0.12,
    source: "file",
    capturedAt: "2026-06-10 10:18",
    synced: false,
  },
  {
    id: "gnss-005",
    label: "GCP-KUR-16",
    lat: 11.93805,
    lng: 79.80912,
    accuracyM: 0.07,
    source: "ntrip",
    capturedAt: "2026-06-10 10:31",
    synced: false,
  },
];

export function formatArea(sqM: number): string {
  const cents = sqM / 40.4686;
  if (cents >= 100) return `${(sqM / 4046.86).toFixed(2)} ac`;
  return `${cents.toFixed(1)} cents`;
}
