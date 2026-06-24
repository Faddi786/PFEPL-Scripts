import type { ReactNode } from "react";
import IPhoneStatusBar from "./IPhoneStatusBar";
import { useLiveClock } from "./useLiveClock";

/** iPhone 17 Pro Max logical viewport: 440 × 956 pt (+7% presentation scale) */
const PRO_MAX_WIDTH = 471;
const PRO_MAX_HEIGHT = 956;

type Props = {
  children: ReactNode;
  mode?: "lock" | "app";
  theatre?: boolean;
};

export default function PhoneFrame({ children, mode = "lock", theatre = false }: Props) {
  const { time } = useLiveClock();
  const isLock = mode === "lock";
  const maxHeightExpr = theatre ? "92vh" : "calc(100vh - 108px)";

  return (
    <div
      className="relative mx-auto shrink-0"
      style={{
        width: `min(${PRO_MAX_WIDTH}px, calc(${maxHeightExpr} * ${PRO_MAX_WIDTH} / ${PRO_MAX_HEIGHT}))`,
        aspectRatio: `${PRO_MAX_WIDTH} / ${PRO_MAX_HEIGHT}`,
      }}
    >
      <div className="h-full rounded-[3.25rem] border-[5px] border-[#8e8e93] bg-gradient-to-b from-[#d8d8dc] via-[#b8b8bd] to-[#9a9aa0] p-[3px] shadow-[0_32px_80px_rgba(0,0,0,0.45)]">
        <div className="relative h-full overflow-hidden rounded-[2.95rem] bg-black shadow-[inset_0_0_0_1px_rgba(255,255,255,0.12)]">
          <div className="relative flex h-full flex-col overflow-hidden">
            {isLock ? <IPhoneStatusBar time={time} light /> : null}

            {isLock ? (
              <div className="pointer-events-none absolute inset-x-0 top-[calc(4px+2%)] z-50 flex justify-center">
                <div className="h-7 w-24 rounded-[14px] bg-black shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]">
                  <div className="flex h-full items-center justify-between px-3.5">
                    <div className="h-[5px] w-[5px] rounded-full bg-[#101018]/80" />
                    <div className="h-[7px] w-[7px] rounded-full bg-[#0d0d10] ring-1 ring-[#1f1f24]" />
                  </div>
                </div>
              </div>
            ) : null}

            <div className="relative min-h-0 flex-1 overflow-hidden bg-[#F7F7F5]" data-nilam-mobile>
              {children}
            </div>

            <div className="pointer-events-none absolute inset-x-0 bottom-[6px] z-40 flex justify-center">
              <div className="h-[5px] w-[34%] max-w-[140px] rounded-full bg-white/90" />
            </div>
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute -right-[3px] top-[15%] h-[6%] w-[3px] rounded-r-md bg-[#a1a1a6]" />
      <div className="pointer-events-none absolute -right-[3px] top-[22%] h-[9%] w-[3px] rounded-r-md bg-[#a1a1a6]" />
      <div className="pointer-events-none absolute -left-[3px] top-[14%] h-[3.5%] w-[3px] rounded-l-md bg-[#a1a1a6]" />
      <div className="pointer-events-none absolute -left-[3px] top-[19%] h-[6%] w-[3px] rounded-l-md bg-[#a1a1a6]" />
      <div className="pointer-events-none absolute -left-[3px] top-[26%] h-[6%] w-[3px] rounded-l-md bg-[#a1a1a6]" />
    </div>
  );
}
