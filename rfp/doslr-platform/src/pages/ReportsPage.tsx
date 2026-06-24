import { useMemo, useState } from "react";
import { ArrowLeft, BarChart3, ChevronDown, Lightbulb } from "lucide-react";
import { Link } from "react-router-dom";
import ReportFilterDropdown from "../components/reports/ReportFilterDropdown";
import { ReportRegionBar, ReportStatusDonut, ReportTrendBar } from "../components/reports/ReportCharts";
import RbacMatrix from "../components/reports/RbacMatrix";
import {
  ALL_REPORT_MONTH_IDS,
  ALL_REPORT_YEAR_IDS,
  REPORT_DEFINITIONS,
  REPORT_LOOKUP,
  REPORT_MONTH_OPTIONS,
  REPORT_YEAR_OPTIONS,
  buildFilteredReport,
  type KpiCard,
  type ReportId,
} from "../data/reports";

const toneClasses: Record<NonNullable<KpiCard["tone"]>, string> = {
  neutral: "border-slate-200 bg-white",
  success: "border-emerald-200 bg-emerald-50/50",
  warning: "border-amber-200 bg-amber-50/50",
  danger: "border-rose-200 bg-rose-50/50",
  info: "border-sky-200 bg-sky-50/50",
};

function KpiGrid({ items }: { items: KpiCard[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      {items.map((kpi) => (
        <div
          key={kpi.label}
          className={`rounded-2xl border px-4 py-3 ${toneClasses[kpi.tone ?? "neutral"]}`}
        >
          <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{kpi.label}</p>
          <p className="mt-1 text-2xl font-semibold text-[#1A1A1A]">
            {typeof kpi.value === "number" ? kpi.value.toLocaleString() : kpi.value}
          </p>
          {kpi.hint ? <p className="mt-1 text-[11px] text-slate-500">{kpi.hint}</p> : null}
        </div>
      ))}
    </div>
  );
}

export default function ReportsPage() {
  const [reportId, setReportId] = useState<ReportId>("online-mutation");
  const [selectedMonths, setSelectedMonths] = useState<string[]>(ALL_REPORT_MONTH_IDS);
  const [selectedYears, setSelectedYears] = useState<string[]>(ALL_REPORT_YEAR_IDS);

  const baseReport = useMemo(() => REPORT_LOOKUP[reportId] ?? REPORT_DEFINITIONS[0], [reportId]);
  const report = useMemo(
    () => buildFilteredReport(baseReport, selectedMonths, selectedYears),
    [baseReport, selectedMonths, selectedYears],
  );

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#F7F7F5] p-3 lg:p-4">
      <main className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto rounded-2xl border border-white/70 bg-white/85 p-4 shadow-[0_8px_30px_rgba(0,0,0,0.06)] lg:p-5">
        <div className="mb-5 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between xl:gap-6">
          <div className="min-w-0 flex-1">
            <Link
              to="/app"
              className="mb-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 transition hover:text-slate-800"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to map
            </Link>
            <div className="flex items-start gap-2">
              <BarChart3 className="mt-0.5 h-5 w-5 shrink-0 text-slate-700" />
              <div className="min-w-0">
                <h2 className="text-lg font-semibold text-[#1A1A1A]">{report.title}</h2>
                <p className="mt-0.5 max-w-2xl text-xs leading-relaxed text-slate-500">{report.subtitle}</p>
              </div>
            </div>
          </div>

          <div className="flex shrink-0 flex-wrap items-end gap-2 sm:gap-3">
            <div className="w-[calc(50%-0.25rem)] sm:w-[130px]">
              <ReportFilterDropdown
                label="Month"
                options={[...REPORT_MONTH_OPTIONS]}
                selected={selectedMonths}
                onChange={setSelectedMonths}
              />
            </div>

            <div className="w-[calc(50%-0.25rem)] sm:w-[130px]">
              <ReportFilterDropdown
                label="Year"
                options={REPORT_YEAR_OPTIONS}
                selected={selectedYears}
                onChange={setSelectedYears}
              />
            </div>

            <label className="relative block w-full sm:w-[200px]">
              <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Report type
              </span>
              <select
                className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                value={reportId}
                onChange={(event) => setReportId(event.target.value as ReportId)}
              >
                {REPORT_DEFINITIONS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute bottom-2.5 right-3 h-4 w-4 text-slate-400" />
            </label>
          </div>
        </div>

        <KpiGrid items={report.kpis} />

        <div key={`${reportId}-${selectedMonths.join(",")}-${selectedYears.join(",")}`} className="mt-5 grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <ReportStatusDonut data={report.statusBreakdown} title="Status breakdown" />
          <ReportTrendBar data={report.monthlyTrend} title="Monthly volume" />
          <ReportRegionBar
            data={report.regionSplit}
            title={report.id === "search-rbac" ? "Searches by role" : "By region"}
          />
        </div>

        {report.rbacMatrix ? (
          <div className="mt-5">
            <RbacMatrix functions={report.rbacMatrix.functions} roles={report.rbacMatrix.roles} />
          </div>
        ) : null}

        <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
          <div className="mb-2 flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-amber-500" />
            <p className="text-sm font-semibold text-[#1A1A1A]">Key insights</p>
          </div>
          <ul className="space-y-2">
            {report.insights.map((insight) => (
              <li key={insight} className="flex gap-2 text-sm text-slate-600">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                {insight}
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  );
}
