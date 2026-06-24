import { AnimatePresence, motion } from "framer-motion";
import { Bluetooth, Check, CloudUpload, Loader2, MessageSquare, Radio, Wifi } from "lucide-react";
import type { IslandNotification } from "./MobileAppContext";
import { useMobileApp } from "./MobileAppContext";

function IslandIcon({ icon }: { icon: IslandNotification["icon"] }) {
  const className = "h-3.5 w-3.5 text-white";
  switch (icon) {
    case "message":
      return <MessageSquare className={className} />;
    case "wifi":
      return <Wifi className={className} />;
    case "upload":
      return <CloudUpload className={className} />;
    case "bluetooth":
      return <Bluetooth className={className} />;
    case "check":
      return <Check className={className} />;
    case "radio":
      return <Radio className={className} />;
    case "loader":
      return <Loader2 className={`${className} animate-spin`} />;
    default:
      return <div className="h-2 w-2 rounded-full bg-white/80" />;
  }
}

function iconBg(icon: IslandNotification["icon"]) {
  switch (icon) {
    case "check":
    case "wifi":
      return "bg-emerald-500";
    case "upload":
      return "bg-sky-500";
    case "message":
      return "bg-indigo-500";
    case "bluetooth":
    case "radio":
      return "bg-violet-500";
    default:
      return "bg-zinc-600";
  }
}

export default function DynamicIslandNotifier() {
  const { islandNotification } = useMobileApp();
  const expanded = Boolean(islandNotification);

  return (
    <div className="pointer-events-none absolute inset-x-0 top-[calc(4px+2%)] z-50 flex justify-center">
      <motion.div
        layout
        initial={false}
        animate={{
          width: expanded ? 300 : 96,
          height: expanded ? 56 : 28,
          borderRadius: expanded ? 26 : 14,
        }}
        transition={{ type: "spring", stiffness: 420, damping: 34, mass: 0.85 }}
        className="relative overflow-hidden bg-black shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]"
      >
        {!expanded ? (
          <div className="flex h-full items-center justify-between px-3.5">
            <div className="h-[5px] w-[5px] rounded-full bg-[#101018]/80" />
            <div className="h-[7px] w-[7px] rounded-full bg-[#0d0d10] ring-1 ring-[#1f1f24]" />
          </div>
        ) : null}

        <AnimatePresence mode="wait">
          {expanded && islandNotification ? (
            <motion.div
              key={islandNotification.id}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={{ duration: 0.22 }}
              className="flex h-full items-center gap-2.5 px-3.5"
            >
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${iconBg(islandNotification.icon)}`}
              >
                <IslandIcon icon={islandNotification.icon} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[14px] font-semibold leading-tight text-white">{islandNotification.title}</p>
                {islandNotification.subtitle ? (
                  <p className="truncate text-[12px] leading-tight text-white/65">{islandNotification.subtitle}</p>
                ) : null}
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
