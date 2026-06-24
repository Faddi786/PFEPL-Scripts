import { Home, Map, Radio, Search, Upload } from "lucide-react";
import { useState } from "react";
import type { MobileTab } from "../../data/mobileApp";
import DynamicIslandNotifier from "./DynamicIslandNotifier";
import PhoneFrame from "./PhoneFrame";
import { MobileAppProvider, useMobileApp } from "./MobileAppContext";
import MobileCaptureScreen from "./screens/MobileCaptureScreen";
import MobileHomeScreen from "./screens/MobileHomeScreen";
import MobileLockScreen from "./screens/MobileLockScreen";
import MobileLoginScreen from "./screens/MobileLoginScreen";
import MobileMapScreen from "./screens/MobileMapScreen";
import MobileParcelDetailScreen from "./screens/MobileParcelDetailScreen";
import MobileSearchScreen from "./screens/MobileSearchScreen";
import MobileSyncScreen from "./screens/MobileSyncScreen";

const tabs: Array<{ id: MobileTab; label: string; icon: typeof Home }> = [
  { id: "home", label: "Home", icon: Home },
  { id: "map", label: "Map", icon: Map },
  { id: "search", label: "Search", icon: Search },
  { id: "capture", label: "GNSS", icon: Radio },
  { id: "sync", label: "Sync", icon: Upload },
];

function MobileBottomNav() {
  const { tab, setTab } = useMobileApp();

  return (
    <nav className="flex shrink-0 border-t border-slate-200/80 bg-white px-1 pb-[2px] pt-1">
      {tabs.map((item) => {
        const active = tab === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={`flex flex-1 flex-col items-center gap-0.5 rounded-lg py-1.5 transition ${
              active ? "text-[#1A1A1A]" : "text-slate-400"
            }`}
          >
            <item.icon className={`h-4 w-4 ${active ? "stroke-[2.5px]" : ""}`} />
            <span className="text-[9px] font-medium">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

function MobileAppShell({
  phoneUnlocked,
  onPhoneUnlock,
}: {
  phoneUnlocked: boolean;
  onPhoneUnlock: () => void;
}) {
  const { officer, tab, selectedParcelId } = useMobileApp();

  if (!phoneUnlocked) {
    return <MobileLockScreen onUnlock={onPhoneUnlock} />;
  }

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <DynamicIslandNotifier />

      {!officer ? (
        <div className="h-full overflow-hidden pt-[calc(4px+2%+34px)]">
          <MobileLoginScreen />
        </div>
      ) : (
        <>
          <div className="relative min-h-0 flex-1 overflow-hidden pt-[calc(4px+2%+34px)]">
            {tab === "home" ? <MobileHomeScreen /> : null}
            {tab === "map" ? <MobileMapScreen /> : null}
            {tab === "search" ? <MobileSearchScreen /> : null}
            {tab === "capture" ? <MobileCaptureScreen /> : null}
            {tab === "sync" ? <MobileSyncScreen /> : null}
            {selectedParcelId ? <MobileParcelDetailScreen /> : null}
          </div>
          <MobileBottomNav />
        </>
      )}
    </div>
  );
}

type Props = {
  theatre?: boolean;
};

export default function MobileApp({ theatre = false }: Props) {
  const [phoneUnlocked, setPhoneUnlocked] = useState(false);

  return (
    <div className="flex h-full w-full justify-center">
      <PhoneFrame mode={phoneUnlocked ? "app" : "lock"} theatre={theatre}>
        <MobileAppProvider>
          <MobileAppShell phoneUnlocked={phoneUnlocked} onPhoneUnlock={() => setPhoneUnlocked(true)} />
        </MobileAppProvider>
      </PhoneFrame>
    </div>
  );
}
