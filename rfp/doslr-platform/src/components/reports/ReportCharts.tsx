import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartPoint } from "../../data/reports";

/** Executive palette — clear on projector, aligned with KPI semantics (graphs only). */
const CHART = {
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  neutral: "#64748b",
  info: "#3b82f6",
  primary: "#334155",
  accent: "#0284c7",
} as const;

const CHART_STATUS_BY_LABEL: Record<string, string> = {
  Approved: CHART.success,
  Pending: CHART.warning,
  Rejected: CHART.danger,
  Draft: CHART.neutral,
  Committed: CHART.success,
  "QA pending": CHART.warning,
  Reverted: CHART.danger,
  Closed: CHART.success,
  "In progress": CHART.warning,
  "Failed sync": CHART.danger,
  Issued: CHART.info,
  Cancelled: CHART.danger,
  Green: CHART.success,
  Amber: CHART.warning,
  Red: CHART.danger,
  Allowed: CHART.success,
  Denied: CHART.danger,
  Found: CHART.success,
  "Not found": CHART.neutral,
  Success: CHART.success,
  Retry: CHART.warning,
  Failed: CHART.danger,
  Published: CHART.success,
  Review: CHART.warning,
};

const CHART_STATUS_FALLBACK = [
  CHART.success,
  CHART.warning,
  CHART.danger,
  CHART.neutral,
  CHART.info,
  "#6366f1",
];

const CHART_MONTHLY_BAR = CHART.info;
const CHART_REGION_BAR = CHART.accent;

const CHART_REGION_BY_LABEL: Record<string, string> = {
  Puducherry: "#1d4ed8",
  Karaikal: "#0f766e",
  Mahe: "#7c3aed",
  Yanam: "#c2410c",
  Citizen: "#1d4ed8",
  Officer: "#0f766e",
  Admin: "#7c3aed",
};

function chartStatusColor(label: string, index: number) {
  return CHART_STATUS_BY_LABEL[label] ?? CHART_STATUS_FALLBACK[index % CHART_STATUS_FALLBACK.length];
}

type TooltipEntry = {
  name?: string;
  value?: number;
  payload?: Record<string, unknown>;
};

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipEntry[] }) {
  if (!active || !payload?.length) return null;

  const entry = payload[0];
  const item = entry.payload ?? {};
  const label = String(item.label ?? item.name ?? entry.name ?? "");
  const raw = item.value ?? item.count ?? entry.value;

  if (raw === undefined || raw === null) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      {label ? <p className="font-medium text-slate-800">{label}</p> : null}
      <p className="text-slate-600">{typeof raw === "number" ? raw.toLocaleString() : String(raw)}</p>
    </div>
  );
}

const chartBoxClass = "h-[240px] min-h-[240px] w-full min-w-0";

export function ReportStatusDonut({ data, title }: { data: ChartPoint[]; title: string }) {
  if (!data.length) return null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="mb-3 text-sm font-semibold text-[#1A1A1A]">{title}</p>
      <div className={chartBoxClass}>
        <ResponsiveContainer width="100%" height={240} minWidth={0}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius={52}
              outerRadius={82}
              paddingAngle={2}
            >
              {data.map((point, index) => (
                <Cell key={point.label} fill={chartStatusColor(point.label, index)} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function ReportTrendBar({ data, title }: { data: ChartPoint[]; title: string }) {
  if (!data.length) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="mb-3 text-sm font-semibold text-[#1A1A1A]">{title}</p>
        <div className={`${chartBoxClass} flex items-center justify-center text-xs text-slate-500`}>
          Select at least one month and year
        </div>
      </div>
    );
  }

  const chartData = data.map((point) => ({ name: point.label, count: point.value }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="mb-3 text-sm font-semibold text-[#1A1A1A]">{title}</p>
      <div className={chartBoxClass}>
        <ResponsiveContainer width="100%" height={240} minWidth={0}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} height={30} />
            <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="count" fill={CHART_MONTHLY_BAR} radius={[6, 6, 0, 0]} name="Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function ReportRegionBar({ data, title }: { data: ChartPoint[]; title: string }) {
  if (!data.length) return null;

  const chartData = data.map((point) => ({ name: point.label, count: point.value }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="mb-3 text-sm font-semibold text-[#1A1A1A]">{title}</p>
      <div className={chartBoxClass}>
        <ResponsiveContainer width="100%" height={240} minWidth={0}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis type="category" dataKey="name" width={72} tick={{ fontSize: 11, fill: "#64748b" }} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="count" fill={CHART_REGION_BAR} radius={[0, 6, 6, 0]} name="Count">
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={CHART_REGION_BY_LABEL[entry.name] ?? CHART_REGION_BAR}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
