import { ArrowLeft } from "lucide-react";
import { formatArea, getMobileParcel } from "../../../data/mobileApp";
import { useMobileApp } from "../MobileAppContext";

export default function MobileParcelDetailScreen() {
  const { selectedParcelId, closeParcel } = useMobileApp();
  const parcel = selectedParcelId ? getMobileParcel(selectedParcelId) : undefined;

  if (!parcel) return null;

  const fields = [
    { label: "Survey No", value: `${parcel.surveyNo}/${parcel.subDiv}` },
    { label: "ULPIN", value: parcel.ulpin },
    { label: "Village", value: parcel.village },
    { label: "Taluk", value: parcel.taluk },
    { label: "Classification", value: parcel.classification },
    { label: "Land use", value: parcel.landUse },
    { label: "Extent", value: `${parcel.areaSqM.toLocaleString()} sq.m (${formatArea(parcel.areaSqM)})` },
    { label: "Owner", value: parcel.owner },
    { label: "Status", value: parcel.status },
    { label: "FMB sheet", value: parcel.fmbSheet },
    { label: "Variance", value: `${parcel.variancePct}% (${parcel.varianceBand})` },
    { label: "Mutation ref", value: parcel.mutationRef },
  ];

  return (
    <div className="absolute inset-0 z-30 flex flex-col bg-[#F7F7F5]">
      <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2.5">
        <button type="button" onClick={closeParcel} className="rounded-lg p-1.5 hover:bg-slate-100">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <p className="text-sm font-semibold text-[#1A1A1A]">
            {parcel.surveyNo}/{parcel.subDiv}
          </p>
          <p className="text-[10px] text-slate-500">Read-only attributes</p>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="mb-3 rounded-2xl border border-slate-200 bg-white p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">RoR snapshot</p>
          <p className="mt-1 text-xs text-slate-600">Synced from Nilamagal · {parcel.lastSurvey}</p>
        </div>

        <div className="space-y-2">
          {fields.map((field) => (
            <div key={field.label} className="rounded-xl border border-slate-100 bg-white px-3 py-2.5">
              <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{field.label}</p>
              <p className="mt-0.5 text-sm text-[#1A1A1A]">{field.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
