import { useEffect, useRef, useState } from "react";
import { CloudUpload, Download } from "lucide-react";
import { useMobileApp } from "../MobileAppContext";

const statusLabel: Record<string, string> = {
  assigned: "Assigned",
  downloaded: "Downloaded",
  "in-progress": "In progress",
  synced: "Synced",
};

function delay(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export default function MobileSyncScreen() {
  const { packets, gnssPoints, markGnssSynced, setPacketProgress, pushIslandNotification } = useMobileApp();
  const pending = gnssPoints.filter((p) => !p.synced).length;
  const [syncing, setSyncing] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const progressRef = useRef(62);

  const kurumbapet = packets.find((p) => p.id === "pkt-kuru-042");
  const progress = kurumbapet?.progressPct ?? 62;

  useEffect(() => {
    progressRef.current = progress;
  }, [progress]);

  async function handleSync() {
    if (syncing || pending === 0) return;
    setSyncing(true);

    pushIslandNotification({
      title: "Looking for internet…",
      icon: "loader",
      durationMs: 2200,
    });
    await delay(2000);

    pushIslandNotification({
      title: "Connected",
      subtitle: "Wi‑Fi · DoSLR network",
      icon: "wifi",
      durationMs: 2200,
    });
    await delay(900);

    pushIslandNotification({
      title: "Uploading field data…",
      subtitle: `${pending} GNSS points`,
      icon: "upload",
      durationMs: 5000,
    });

    const start = progressRef.current;
    const steps = 18;
    const stepMs = 55;

    for (let i = 1; i <= steps; i += 1) {
      await delay(stepMs);
      const next = Math.round(start + ((100 - start) * i) / steps);
      setPacketProgress("pkt-kuru-042", next, i === steps ? "synced" : "in-progress");
    }

    markGnssSynced();
    await delay(400);

    pushIslandNotification({
      title: "Sync complete",
      subtitle: "Kurumbapet packet uploaded",
      icon: "check",
      durationMs: 3500,
    });

    setSyncing(false);
  }

  async function handleDownloadOffline(packetId: string) {
    const packet = packets.find((p) => p.id === packetId);
    if (!packet || packet.status !== "assigned" || downloadingId || syncing) return;

    setDownloadingId(packetId);

    pushIslandNotification({
      title: "Downloading for offline…",
      subtitle: packet.village,
      icon: "loader",
      durationMs: 3200,
    });

    const steps = 20;
    const stepMs = 150;

    for (let i = 1; i <= steps; i += 1) {
      await delay(stepMs);
      const next = Math.round((100 * i) / steps);
      setPacketProgress(packetId, next);
    }

    setPacketProgress(packetId, 100, "downloaded");

    pushIslandNotification({
      title: "Offline download successful",
      subtitle: packet.village,
      icon: "check",
      durationMs: 3500,
    });

    setDownloadingId(null);
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="border-b border-slate-200 bg-white px-4 py-3">
        <p className="text-sm font-semibold text-[#1A1A1A]">Field sync</p>
        <p className="text-[10px] text-slate-500">Offline packets · GNSS upload to WebGIS</p>
      </div>

      <div className="p-4">
        <div className="mb-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-[#1A1A1A]">Upload queue</p>
              <p className="text-xs text-slate-500">
                {pending} GNSS point{pending === 1 ? "" : "s"} pending
              </p>
            </div>
            <button
              type="button"
              onClick={handleSync}
              disabled={pending === 0 || syncing}
              className="flex items-center gap-1.5 rounded-full bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-white disabled:bg-slate-300"
            >
              <CloudUpload className="h-3.5 w-3.5" />
              {syncing ? "Syncing…" : "Sync now"}
            </button>
          </div>
        </div>

        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Field packets</p>
        <div className="space-y-2">
          {packets.map((packet) => (
            <div key={packet.id} className="rounded-xl border border-slate-200 bg-white p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-[#1A1A1A]">{packet.village}</p>
                  <p className="text-[11px] text-slate-500">
                    {packet.parcelCount} parcels · due {packet.dueDate}
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700">
                  {statusLabel[packet.status]}
                </span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-[#1A1A1A] transition-[width] duration-150 ease-linear"
                  style={{ width: `${packet.progressPct}%` }}
                />
              </div>
              {packet.status === "assigned" ? (
                <button
                  type="button"
                  onClick={() => handleDownloadOffline(packet.id)}
                  disabled={downloadingId === packet.id}
                  className="mt-2 flex items-center gap-1 text-[11px] font-medium text-sky-700 disabled:text-slate-400"
                >
                  <Download className="h-3 w-3" />
                  {downloadingId === packet.id ? "Downloading…" : "Download for offline"}
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
