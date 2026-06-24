import { useState } from "react";
import { Search } from "lucide-react";
import { searchMobileParcels } from "../../../data/mobileApp";
import { useMobileApp } from "../MobileAppContext";

export default function MobileSearchScreen() {
  const { openParcel } = useMobileApp();
  const [query, setQuery] = useState("");
  const results = searchMobileParcels(query);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 bg-white px-4 py-3">
        <p className="text-sm font-semibold text-[#1A1A1A]">Parcel search</p>
        <p className="text-[10px] text-slate-500">Survey No · Sub-div · ULPIN</p>
        <div className="mt-2 flex items-center gap-2 rounded-xl border border-slate-200 bg-[#F7F7F5] px-3">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. 142 / 1A / ULPIN"
            className="h-10 w-full bg-transparent text-sm outline-none"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {results.length === 0 ? (
          <p className="py-8 text-center text-xs text-slate-500">No parcels match your search.</p>
        ) : (
          <div className="space-y-2">
            {results.map((parcel) => (
              <button
                key={parcel.id}
                type="button"
                onClick={() => openParcel(parcel.id)}
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-left transition active:bg-slate-50"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-[#1A1A1A]">
                      {parcel.surveyNo}/{parcel.subDiv}
                    </p>
                    <p className="text-[11px] text-slate-500">{parcel.village}</p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      parcel.varianceBand === "green"
                        ? "bg-emerald-100 text-emerald-800"
                        : parcel.varianceBand === "amber"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {parcel.variancePct}% var
                  </span>
                </div>
                <p className="mt-1 truncate text-[10px] text-slate-400">{parcel.ulpin}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
