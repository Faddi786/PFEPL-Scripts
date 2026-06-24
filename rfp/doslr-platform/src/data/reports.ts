import type { WorkflowId } from "./workflows";

export type ReportId = WorkflowId;

export type KpiCard = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
};

export type ChartPoint = { label: string; value: number };

export type RbacRole = {
  role: string;
  description: string;
  users: number;
  permissions: Record<string, boolean>;
};

export type ReportDefinition = {
  id: ReportId;
  title: string;
  subtitle: string;
  period: string;
  kpis: KpiCard[];
  statusBreakdown: ChartPoint[];
  monthlyTrend: ChartPoint[];
  regionSplit: ChartPoint[];
  insights: string[];
  rbacMatrix?: {
    functions: string[];
    roles: RbacRole[];
  };
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

const RBAC_FUNCTIONS = [
  "View parcel map",
  "View owner (full)",
  "View owner (masked)",
  "Submit mutation",
  "Approve mutation",
  "Reject mutation",
  "Export GeoJSON",
  "Certified extract",
  "Georef commit",
  "Field sync",
  "Anomaly triage",
  "Admin config",
];

const RBAC_ROLES: RbacRole[] = [
  {
    role: "Citizen",
    description: "Public portal user with scoped search only",
    users: 12480,
    permissions: {
      "View parcel map": true,
      "View owner (full)": false,
      "View owner (masked)": true,
      "Submit mutation": true,
      "Approve mutation": false,
      "Reject mutation": false,
      "Export GeoJSON": false,
      "Certified extract": true,
      "Georef commit": false,
      "Field sync": false,
      "Anomaly triage": false,
      "Admin config": false,
    },
  },
  {
    role: "Village Officer",
    description: "First-line verification and field packet review",
    users: 186,
    permissions: {
      "View parcel map": true,
      "View owner (full)": true,
      "View owner (masked)": true,
      "Submit mutation": true,
      "Approve mutation": false,
      "Reject mutation": false,
      "Export GeoJSON": true,
      "Certified extract": true,
      "Georef commit": false,
      "Field sync": true,
      "Anomaly triage": true,
      "Admin config": false,
    },
  },
  {
    role: "Tahsildar",
    description: "Approving authority for mutations and extracts",
    users: 42,
    permissions: {
      "View parcel map": true,
      "View owner (full)": true,
      "View owner (masked)": true,
      "Submit mutation": true,
      "Approve mutation": true,
      "Reject mutation": true,
      "Export GeoJSON": true,
      "Certified extract": true,
      "Georef commit": true,
      "Field sync": true,
      "Anomaly triage": true,
      "Admin config": false,
    },
  },
  {
    role: "Surveyor / GIS",
    description: "Cadastral editing, georeferencing and anomaly resolution",
    users: 28,
    permissions: {
      "View parcel map": true,
      "View owner (full)": true,
      "View owner (masked)": true,
      "Submit mutation": false,
      "Approve mutation": false,
      "Reject mutation": false,
      "Export GeoJSON": true,
      "Certified extract": false,
      "Georef commit": true,
      "Field sync": true,
      "Anomaly triage": true,
      "Admin config": false,
    },
  },
  {
    role: "Minister / Read-only",
    description: "Executive dashboard and aggregate reports",
    users: 6,
    permissions: {
      "View parcel map": true,
      "View owner (full)": false,
      "View owner (masked)": true,
      "Submit mutation": false,
      "Approve mutation": false,
      "Reject mutation": false,
      "Export GeoJSON": false,
      "Certified extract": false,
      "Georef commit": false,
      "Field sync": false,
      "Anomaly triage": false,
      "Admin config": false,
    },
  },
  {
    role: "System Admin",
    description: "Platform configuration and audit oversight",
    users: 4,
    permissions: {
      "View parcel map": true,
      "View owner (full)": true,
      "View owner (masked)": true,
      "Submit mutation": true,
      "Approve mutation": true,
      "Reject mutation": true,
      "Export GeoJSON": true,
      "Certified extract": true,
      "Georef commit": true,
      "Field sync": true,
      "Anomaly triage": true,
      "Admin config": true,
    },
  },
];

function trend(base: number, growth = 1.08) {
  return MONTHS.map((label, index) => ({
    label,
    value: Math.round(base * growth ** index),
  }));
}

export const REPORT_DEFINITIONS: ReportDefinition[] = [
  {
    id: "online-mutation",
    title: "Mutation",
    subtitle: "Citizen-to-officer mutation pipeline throughput and decision outcomes",
    period: "Last 6 months · Puducherry UT",
    kpis: [
      { label: "Total submitted", value: 1842, tone: "info" },
      { label: "Approved", value: 1264, tone: "success", hint: "68.6% approval rate" },
      { label: "Pending review", value: 318, tone: "warning" },
      { label: "Rejected", value: 186, tone: "danger" },
      { label: "Synced to Nilamagal", value: 1198, tone: "success" },
      { label: "Avg turnaround", value: "4.2 days", tone: "neutral" },
    ],
    statusBreakdown: [
      { label: "Approved", value: 1264 },
      { label: "Pending", value: 318 },
      { label: "Rejected", value: 186 },
      { label: "Draft", value: 74 },
    ],
    monthlyTrend: trend(240),
    regionSplit: [
      { label: "Puducherry", value: 892 },
      { label: "Karaikal", value: 412 },
      { label: "Mahe", value: 198 },
      { label: "Yanam", value: 340 },
    ],
    insights: [
      "Subdivision requests account for 54% of all mutations this quarter.",
      "Oulgaret taluk has the highest pending queue (86 cases).",
      "Rejection rate dropped 3.1% after mandatory document checklist rollout.",
    ],
  },
  {
    id: "georeferencing",
    title: "Georeferencing",
    subtitle: "FMB sheet alignment, GCP placement and commit/revert outcomes",
    period: "Last 6 months · Cadastral revision programme",
    kpis: [
      { label: "Sheets uploaded", value: 486, tone: "info" },
      { label: "Committed", value: 362, tone: "success" },
      { label: "Pending QA", value: 78, tone: "warning" },
      { label: "Reverted", value: 46, tone: "danger" },
      { label: "Avg RMSE", value: "0.18 m", tone: "success" },
      { label: "GCP pairs placed", value: 2144, tone: "neutral" },
    ],
    statusBreakdown: [
      { label: "Committed", value: 362 },
      { label: "QA pending", value: 78 },
      { label: "Reverted", value: 46 },
    ],
    monthlyTrend: trend(52, 1.06),
    regionSplit: [
      { label: "Puducherry", value: 218 },
      { label: "Karaikal", value: 124 },
      { label: "Mahe", value: 68 },
      { label: "Yanam", value: 76 },
    ],
    insights: [
      "94% of commits passed RMSE threshold on first dry-run.",
      "Sheet PY-FMB-07 had the highest rework count (4 reverts).",
      "Ortho overlay preview reduced revert rate by 22%.",
    ],
  },
  {
    id: "certified-extract",
    title: "Certified Extract",
    subtitle: "Issuance pipeline for attested parcel extracts",
    period: "Last 6 months · Document services",
    kpis: [
      { label: "Extracts requested", value: 956, tone: "info" },
      { label: "Issued & sealed", value: 812, tone: "success" },
      { label: "Awaiting attestation", value: 98, tone: "warning" },
      { label: "Cancelled", value: 46, tone: "danger" },
      { label: "Digital copies", value: 684, tone: "neutral" },
      { label: "Avg issue time", value: "1.6 days", tone: "success" },
    ],
    statusBreakdown: [
      { label: "Issued", value: 812 },
      { label: "Pending", value: 98 },
      { label: "Cancelled", value: 46 },
    ],
    monthlyTrend: trend(128, 1.04),
    regionSplit: [
      { label: "Puducherry", value: 468 },
      { label: "Karaikal", value: 214 },
      { label: "Mahe", value: 118 },
      { label: "Yanam", value: 156 },
    ],
    insights: [
      "Citizen self-service requests grew 18% month-on-month.",
      "Bank lien disclosures appear on 12% of issued extracts.",
      "Audit lock prevented 3 duplicate seal attempts this quarter.",
    ],
  },
  {
    id: "anomaly-pipeline",
    title: "Anomaly Pipeline",
    subtitle: "Automated variance detection and officer triage",
    period: "Last 6 months · Quality assurance",
    kpis: [
      { label: "Flags raised", value: 1428, tone: "info" },
      { label: "Resolved", value: 986, tone: "success" },
      { label: "Under triage", value: 312, tone: "warning" },
      { label: "Escalated", value: 130, tone: "danger" },
      { label: "Green band", value: "62%", tone: "success" },
      { label: "Red band", value: "11%", tone: "danger" },
    ],
    statusBreakdown: [
      { label: "Green", value: 886 },
      { label: "Amber", value: 412 },
      { label: "Red", value: 130 },
    ],
    monthlyTrend: trend(198, 1.03),
    regionSplit: [
      { label: "Puducherry", value: 612 },
      { label: "Karaikal", value: 318 },
      { label: "Mahe", value: 224 },
      { label: "Yanam", value: 274 },
    ],
    insights: [
      "Overlap anomalies dominate Karaikal ward clusters (38% of flags).",
      "Officer triage SLA met for 87% of amber-band cases.",
      "CollabLand baseline drift caused 6% of red-band escalations.",
    ],
  },
  {
    id: "search-rbac",
    title: "Search + RBAC",
    subtitle: "Role-based access, search policy enforcement and audit coverage",
    period: "Last 6 months · Security & access",
    kpis: [
      { label: "Search events", value: 28460, tone: "info" },
      { label: "Policy allowed", value: 27124, tone: "success" },
      { label: "Policy denied", value: 1336, tone: "danger" },
      { label: "Masked owner views", value: 19840, tone: "warning" },
      { label: "Active roles", value: 6, tone: "neutral" },
      { label: "Audit log coverage", value: "100%", tone: "success" },
    ],
    statusBreakdown: [
      { label: "Allowed", value: 27124 },
      { label: "Denied", value: 1336 },
    ],
    monthlyTrend: trend(3800, 1.02),
    regionSplit: [
      { label: "Citizen", value: 19840 },
      { label: "Village Officer", value: 4620 },
      { label: "Tahsildar", value: 2140 },
      { label: "Surveyor", value: 1860 },
    ],
    insights: [
      "Citizen role accounts for 70% of search volume with masked owner fields.",
      "Full owner visibility restricted to Tahsildar and Surveyor roles only.",
      "Denied events spike on weekends due to expired session tokens.",
    ],
    rbacMatrix: { functions: RBAC_FUNCTIONS, roles: RBAC_ROLES },
  },
  {
    id: "citizen-search",
    title: "Citizen Search",
    subtitle: "Public parcel lookup and extract request funnel",
    period: "Last 6 months · Citizen portal",
    kpis: [
      { label: "Total searches", value: 19840, tone: "info" },
      { label: "Parcel found", value: 18612, tone: "success" },
      { label: "Not found", value: 1228, tone: "warning" },
      { label: "Extract requested", value: 2846, tone: "neutral" },
      { label: "ULPIN lookups", value: 6420, tone: "neutral" },
      { label: "Survey no lookups", value: 13420, tone: "neutral" },
    ],
    statusBreakdown: [
      { label: "Found", value: 18612 },
      { label: "Not found", value: 1228 },
    ],
    monthlyTrend: trend(2800, 1.05),
    regionSplit: [
      { label: "Puducherry", value: 9840 },
      { label: "Karaikal", value: 4120 },
      { label: "Mahe", value: 2480 },
      { label: "Yanam", value: 3400 },
    ],
    insights: [
      "Mobile traffic represents 74% of citizen searches.",
      "Top query pattern: survey number with ward filter.",
      "Extract conversion rate is 14.3% from successful searches.",
    ],
  },
  {
    id: "mutation-sync-back",
    title: "Mutation Sync-Back",
    subtitle: "Ledger sync after approved mutations",
    period: "Last 6 months · Integration layer",
    kpis: [
      { label: "Queued", value: 1264, tone: "info" },
      { label: "Sync success", value: 1198, tone: "success" },
      { label: "Retry pending", value: 48, tone: "warning" },
      { label: "Failed", value: 18, tone: "danger" },
      { label: "Avg latency", value: "12 min", tone: "success" },
      { label: "Ack received", value: "99.2%", tone: "success" },
    ],
    statusBreakdown: [
      { label: "Success", value: 1198 },
      { label: "Retry", value: 48 },
      { label: "Failed", value: 18 },
    ],
    monthlyTrend: trend(168, 1.04),
    regionSplit: [
      { label: "Puducherry", value: 612 },
      { label: "Karaikal", value: 286 },
      { label: "Mahe", value: 148 },
      { label: "Yanam", value: 218 },
    ],
    insights: [
      "Nilamagal acknowledgement within SLA for 99.2% of transactions.",
      "Failed syncs correlate with legacy deed reference mismatches.",
      "Nightly batch clears 96% of retry queue automatically.",
    ],
  },
  {
    id: "field-georeferencing",
    title: "Field Georeferencing",
    subtitle: "DGPS capture, residual review and publication",
    period: "Last 6 months · Field geodesy",
    kpis: [
      { label: "DGPS sessions", value: 384, tone: "info" },
      { label: "Published", value: 298, tone: "success" },
      { label: "Pending review", value: 62, tone: "warning" },
      { label: "Rejected", value: 24, tone: "danger" },
      { label: "Avg residual", value: "0.09 m", tone: "success" },
      { label: "GCP pairs verified", value: 1152, tone: "neutral" },
    ],
    statusBreakdown: [
      { label: "Published", value: 298 },
      { label: "Review", value: 62 },
      { label: "Rejected", value: 24 },
    ],
    monthlyTrend: trend(48, 1.07),
    regionSplit: [
      { label: "Puducherry", value: 168 },
      { label: "Karaikal", value: 86 },
      { label: "Mahe", value: 64 },
      { label: "Yanam", value: 66 },
    ],
    insights: [
      "RTK captures outperform DGPS by 40% on first-pass acceptance.",
      "Residuals above 0.25 m trigger automatic officer review.",
      "Publication backlog cleared within 5 days on average.",
    ],
  },
];

export const REPORT_LOOKUP = Object.fromEntries(REPORT_DEFINITIONS.map((report) => [report.id, report]));

export const STATUS_COLORS = ["#16a34a", "#f59e0b", "#ef4444", "#64748b", "#0ea5e9", "#8b5cf6"];

export const REPORT_MONTH_OPTIONS = [
  { id: "01", label: "January" },
  { id: "02", label: "February" },
  { id: "03", label: "March" },
  { id: "04", label: "April" },
  { id: "05", label: "May" },
  { id: "06", label: "June" },
  { id: "07", label: "July" },
  { id: "08", label: "August" },
  { id: "09", label: "September" },
  { id: "10", label: "October" },
  { id: "11", label: "November" },
  { id: "12", label: "December" },
] as const;

export const REPORT_YEAR_OPTIONS = Array.from({ length: 11 }, (_, index) => {
  const year = String(2026 + index);
  return { id: year, label: year };
});

export const ALL_REPORT_MONTH_IDS = REPORT_MONTH_OPTIONS.map((month) => month.id);
export const ALL_REPORT_YEAR_IDS = REPORT_YEAR_OPTIONS.map((year) => year.id);

const MONTH_SHORT: Record<string, string> = {
  "01": "Jan",
  "02": "Feb",
  "03": "Mar",
  "04": "Apr",
  "05": "May",
  "06": "Jun",
  "07": "Jul",
  "08": "Aug",
  "09": "Sep",
  "10": "Oct",
  "11": "Nov",
  "12": "Dec",
};

function filterSeed(reportId: string, monthId: string, year: string, salt: string) {
  let seed = 0;
  const text = `${reportId}-${monthId}-${year}-${salt}`;
  for (let i = 0; i < text.length; i += 1) {
    seed = (seed * 31 + text.charCodeAt(i)) >>> 0;
  }
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}

function filterRatio(selectedMonths: string[], selectedYears: string[]) {
  const total = ALL_REPORT_MONTH_IDS.length * ALL_REPORT_YEAR_IDS.length;
  if (total === 0) return 0;
  return (selectedMonths.length * selectedYears.length) / total;
}

function scalePoints(points: ChartPoint[], ratio: number): ChartPoint[] {
  if (ratio <= 0) return points.map((point) => ({ ...point, value: 0 }));
  return points.map((point) => ({ ...point, value: Math.max(0, Math.round(point.value * ratio)) }));
}

function scaleKpis(kpis: KpiCard[], ratio: number): KpiCard[] {
  return kpis.map((kpi) => {
    if (typeof kpi.value === "number") {
      return { ...kpi, value: Math.max(0, Math.round(kpi.value * ratio)) };
    }
    return kpi;
  });
}

function buildMonthlyTrend(report: ReportDefinition, selectedMonths: string[], selectedYears: string[]): ChartPoint[] {
  const sortedMonths = REPORT_MONTH_OPTIONS.filter((month) => selectedMonths.includes(month.id));
  const sortedYears = REPORT_YEAR_OPTIONS.filter((year) => selectedYears.includes(year.id));

  if (sortedMonths.length === 0 || sortedYears.length === 0) {
    return [];
  }

  const baseAvg =
    report.monthlyTrend.reduce((sum, point) => sum + point.value, 0) / Math.max(report.monthlyTrend.length, 1);

  return sortedMonths.map((month) => {
    const value = sortedYears.reduce((sum, year, yearIndex) => {
      const jitter = 0.82 + filterSeed(report.id, month.id, year.id, "monthly") * 0.36;
      const yearFactor = 1 + yearIndex * 0.035;
      return sum + Math.round(baseAvg * yearFactor * jitter);
    }, 0);

    return {
      label: MONTH_SHORT[month.id],
      value,
    };
  });
}

function formatPeriodLabel(selectedMonths: string[], selectedYears: string[]) {
  if (selectedMonths.length === ALL_REPORT_MONTH_IDS.length && selectedYears.length === ALL_REPORT_YEAR_IDS.length) {
    return "Jan 2026 – Dec 2036 · Puducherry UT";
  }
  if (selectedMonths.length === 0 || selectedYears.length === 0) {
    return "No period selected";
  }
  const monthPart =
    selectedMonths.length === ALL_REPORT_MONTH_IDS.length
      ? "All months"
      : `${selectedMonths.length} month${selectedMonths.length > 1 ? "s" : ""}`;
  const yearPart =
    selectedYears.length === 1
      ? selectedYears[0]
      : selectedYears.length === ALL_REPORT_YEAR_IDS.length
        ? "2026–2036"
        : `${selectedYears.length} years`;
  return `${monthPart} · ${yearPart} · Puducherry UT`;
}

export function buildFilteredReport(
  report: ReportDefinition,
  selectedMonths: string[],
  selectedYears: string[],
): ReportDefinition {
  const ratio = filterRatio(selectedMonths, selectedYears);

  return {
    ...report,
    period: formatPeriodLabel(selectedMonths, selectedYears),
    kpis: scaleKpis(report.kpis, ratio),
    statusBreakdown: scalePoints(report.statusBreakdown, ratio),
    monthlyTrend: buildMonthlyTrend(report, selectedMonths, selectedYears),
    regionSplit: scalePoints(report.regionSplit, ratio),
  };
}
