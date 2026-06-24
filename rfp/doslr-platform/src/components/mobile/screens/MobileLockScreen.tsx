import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronUp } from "lucide-react";
import AppleLogo from "../AppleLogo";
import { useLiveClock } from "../useLiveClock";

type Props = {
  onUnlock: () => void;
};

export default function MobileLockScreen({ onUnlock }: Props) {
  const [unlocking, setUnlocking] = useState(false);
  const { dateLine, lockTimeLarge } = useLiveClock();

  useEffect(() => {
    if (!unlocking) return;
    const timer = window.setTimeout(onUnlock, 520);
    return () => window.clearTimeout(timer);
  }, [unlocking, onUnlock]);

  return (
    <button
      type="button"
      onClick={() => setUnlocking(true)}
      className="relative flex h-full w-full flex-col overflow-hidden bg-black text-left"
      aria-label="Swipe up to unlock"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(99,102,241,0.22),transparent_42%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.16),transparent_36%),linear-gradient(180deg,#0b0b10_0%,#15151c_45%,#09090d_100%)]" />

      <AnimatePresence>
        {!unlocking ? (
          <motion.div
            key="lock"
            initial={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -120 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 flex h-full flex-col pt-[52px]"
          >
            <div className="flex flex-1 flex-col items-center justify-center px-6">
              <p className="text-[15px] font-medium text-white/75">{dateLine}</p>
              <p className="mt-1 text-[clamp(3.5rem,14vw,4.75rem)] font-thin leading-none tracking-[-0.04em] text-white">
                {lockTimeLarge}
              </p>
              <div className="mt-10">
                <AppleLogo />
              </div>
            </div>

            <div className="flex flex-col items-center gap-1 pb-10 text-white/85">
              <ChevronUp className="h-5 w-5 animate-bounce" />
              <span className="text-sm font-medium">Tap to open</span>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </button>
  );
}
