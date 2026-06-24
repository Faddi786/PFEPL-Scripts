import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  DEMO_FIELD_OFFICER,
  FIELD_PACKETS,
  INITIAL_GNSS_POINTS,
  type CapturedGnssPoint,
  type FieldOfficer,
  type FieldPacket,
  type MobileTab,
} from "../../data/mobileApp";

export type IslandNotification = {
  id: string;
  title: string;
  subtitle?: string;
  icon?: "message" | "wifi" | "loader" | "upload" | "bluetooth" | "check" | "radio";
  durationMs?: number;
};

type MobileAppState = {
  officer: FieldOfficer | null;
  tab: MobileTab;
  selectedParcelId: string | null;
  gnssConnected: boolean;
  gnssPoints: CapturedGnssPoint[];
  packets: FieldPacket[];
  islandNotification: IslandNotification | null;
  login: (userId: string) => void;
  logout: () => void;
  setTab: (tab: MobileTab) => void;
  openParcel: (id: string) => void;
  closeParcel: () => void;
  connectGnss: () => void;
  disconnectGnss: () => void;
  captureGnssPoint: () => void;
  setPacketProgress: (id: string, progressPct: number, status?: FieldPacket["status"]) => void;
  markGnssSynced: () => void;
  downloadPacket: (id: string) => void;
  pushIslandNotification: (notification: Omit<IslandNotification, "id">) => void;
  clearIslandNotification: () => void;
};

const MobileAppContext = createContext<MobileAppState | null>(null);

export function MobileAppProvider({ children }: { children: ReactNode }) {
  const [officer, setOfficer] = useState<FieldOfficer | null>(null);
  const [tab, setTab] = useState<MobileTab>("home");
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  const [gnssConnected, setGnssConnected] = useState(false);
  const [gnssPoints, setGnssPoints] = useState<CapturedGnssPoint[]>(INITIAL_GNSS_POINTS);
  const [packets, setPackets] = useState<FieldPacket[]>(FIELD_PACKETS);
  const [islandNotification, setIslandNotification] = useState<IslandNotification | null>(null);
  const dismissTimer = useRef<number | null>(null);

  const clearIslandNotification = useCallback(() => {
    if (dismissTimer.current) {
      window.clearTimeout(dismissTimer.current);
      dismissTimer.current = null;
    }
    setIslandNotification(null);
  }, []);

  const pushIslandNotification = useCallback(
    (notification: Omit<IslandNotification, "id">) => {
      if (dismissTimer.current) window.clearTimeout(dismissTimer.current);
      const next: IslandNotification = { ...notification, id: `island-${Date.now()}` };
      setIslandNotification(next);
      const duration = notification.durationMs ?? 4500;
      dismissTimer.current = window.setTimeout(() => {
        setIslandNotification((current) => (current?.id === next.id ? null : current));
        dismissTimer.current = null;
      }, duration);
    },
    [],
  );

  const setPacketProgress = useCallback((id: string, progressPct: number, status?: FieldPacket["status"]) => {
    setPackets((prev) =>
      prev.map((pkt) =>
        pkt.id === id
          ? {
              ...pkt,
              progressPct,
              ...(status ? { status } : {}),
            }
          : pkt,
      ),
    );
  }, []);

  const markGnssSynced = useCallback(() => {
    setGnssPoints((prev) => prev.map((p) => ({ ...p, synced: true })));
  }, []);

  const value = useMemo<MobileAppState>(
    () => ({
      officer,
      tab,
      selectedParcelId,
      gnssConnected,
      gnssPoints,
      packets,
      islandNotification,
      login: (userId: string) => {
        setOfficer({
          ...DEMO_FIELD_OFFICER,
          id: userId || DEMO_FIELD_OFFICER.id,
        });
        setTab("home");
      },
      logout: () => {
        setOfficer(null);
        setSelectedParcelId(null);
        setTab("home");
        clearIslandNotification();
      },
      setTab,
      openParcel: (id: string) => setSelectedParcelId(id),
      closeParcel: () => setSelectedParcelId(null),
      connectGnss: () => {
        pushIslandNotification({
          title: "Searching for rover…",
          subtitle: "Bluetooth pairing",
          icon: "loader",
          durationMs: 1800,
        });
        window.setTimeout(() => {
          setGnssConnected(true);
          pushIslandNotification({
            title: "Trimble R12 connected",
            subtitle: "RTK fix · ±0.09 m",
            icon: "check",
            durationMs: 3500,
          });
        }, 1800);
      },
      disconnectGnss: () => {
        setGnssConnected(false);
        pushIslandNotification({
          title: "Rover disconnected",
          icon: "radio",
          durationMs: 2500,
        });
      },
      captureGnssPoint: () => {
        if (!gnssConnected) return;
        const next: CapturedGnssPoint = {
          id: `gnss-${Date.now()}`,
          label: `GCP-KUR-${String(gnssPoints.length + 1).padStart(2, "0")}`,
          lat: 11.9374 + (Math.random() - 0.5) * 0.002,
          lng: 79.8083 + (Math.random() - 0.5) * 0.002,
          accuracyM: Number((0.06 + Math.random() * 0.12).toFixed(2)),
          source: "bluetooth",
          capturedAt: new Date().toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          }),
          synced: false,
        };
        setGnssPoints((prev) => [next, ...prev]);
        pushIslandNotification({
          title: "Control point captured",
          subtitle: next.label,
          icon: "check",
          durationMs: 2800,
        });
      },
      setPacketProgress,
      markGnssSynced,
      downloadPacket: (id: string) => {
        setPackets((prev) =>
          prev.map((pkt) => (pkt.id === id && pkt.status === "assigned" ? { ...pkt, status: "downloaded" } : pkt)),
        );
      },
      pushIslandNotification,
      clearIslandNotification,
    }),
    [
      officer,
      tab,
      selectedParcelId,
      gnssConnected,
      gnssPoints,
      packets,
      islandNotification,
      setPacketProgress,
      markGnssSynced,
      pushIslandNotification,
      clearIslandNotification,
    ],
  );

  useEffect(
    () => () => {
      if (dismissTimer.current) window.clearTimeout(dismissTimer.current);
    },
    [],
  );

  return <MobileAppContext.Provider value={value}>{children}</MobileAppContext.Provider>;
}

export function useMobileApp() {
  const ctx = useContext(MobileAppContext);
  if (!ctx) throw new Error("useMobileApp must be used within MobileAppProvider");
  return ctx;
}
