import { ChevronRight, Map, Power, Radio, Search, Upload } from "lucide-react";
import { useMobileApp } from "../MobileAppContext";

export default function MobileHomeScreen() {
  const { officer, gnssPoints, packets, setTab, logout } = useMobileApp();
  if (!officer) return null;

  const pendingSync = gnssPoints.filter((p) => !p.synced).length;
  const activePacket = packets.find((p) => p.status === "in-progress");

  return (
    <div className="h-full overflow-y-auto px-4 pb-4 pt-1">
      <div className="mb-4 flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-slate-500">Welcome back</p>
          <h2 className="text-2xl font-semibold tracking-tight text-[#1A1A1A]">{officer.name}</h2>
          <p className="text-xs text-slate-500">
            {officer.role} · {officer.badge}
          </p>
        </div>
        <button
          type="button"
          onClick={logout}
          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-rose-200/80 bg-rose-50/40 transition hover:border-rose-300/80 hover:bg-rose-50/60 active:scale-95"
          title="Sign out"
          aria-label="Sign out"
        >
          <Power className="h-3.5 w-3.5 text-rose-400/70" strokeWidth={2} />
        </button>
      </div>

      <div className="mb-4 rounded-2xl border border-slate-200 bg-white p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Assigned area</p>
        <p className="mt-1 text-sm font-semibold text-[#1A1A1A]">{officer.assignedVillage}</p>
        <p className="text-xs text-slate-500">
          {officer.assignedTaluk} · {officer.region}
        </p>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-2">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-2.5 text-center">
          <p className="text-lg font-semibold text-[#1A1A1A]">{activePacket?.progressPct ?? 0}%</p>
          <p className="text-[10px] text-slate-500">Packet done</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-2.5 text-center">
          <p className="text-lg font-semibold text-[#1A1A1A]">{gnssPoints.length}</p>
          <p className="text-[10px] text-slate-500">GNSS points</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-2.5 text-center">
          <p className="text-lg font-semibold text-[#1A1A1A]">{pendingSync}</p>
          <p className="text-[10px] text-slate-500">Pending sync</p>
        </div>
      </div>

      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Quick actions</p>
      <div className="space-y-2">
        {[
          { id: "map" as const, label: "Open cadastral map", icon: Map },
          { id: "search" as const, label: "Search parcel", icon: Search },
          { id: "capture" as const, label: "Capture DGPS point", icon: Radio },
          { id: "sync" as const, label: "Sync field data", icon: Upload },
        ].map((action) => (
          <button
            key={action.id}
            type="button"
            onClick={() => setTab(action.id)}
            className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left transition active:bg-slate-50"
          >
            <span className="flex items-center gap-2 text-sm font-medium text-[#1A1A1A]">
              <action.icon className="h-4 w-4 text-slate-500" />
              {action.label}
            </span>
            <ChevronRight className="h-4 w-4 text-slate-400" />
          </button>
        ))}
      </div>
    </div>
  );
}
