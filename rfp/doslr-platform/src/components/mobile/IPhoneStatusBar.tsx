function IosCellular() {
  return (
    <svg width="18" height="12" viewBox="0 0 18 12" fill="none" aria-hidden>
      <rect x="0.5" y="8" width="3" height="3.5" rx="0.6" fill="currentColor" />
      <rect x="4.5" y="5.5" width="3" height="6" rx="0.6" fill="currentColor" />
      <rect x="8.5" y="3" width="3" height="8.5" rx="0.6" fill="currentColor" />
      <rect x="12.5" y="0.5" width="3" height="11" rx="0.6" fill="currentColor" />
    </svg>
  );
}

function IosWifi() {
  return (
    <svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden className="shrink-0">
      <circle cx="8" cy="10.35" r="1" fill="currentColor" />
      <path
        d="M5.35 9.15c1.15-1.15 3.05-1.15 4.2 0"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M3.15 7.05c2.35-2.35 6.25-2.35 8.55 0"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M0.95 4.95c3.5-3.5 9.45-3.5 12.95 0"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

function IosBattery() {
  return (
    <svg width="27" height="13" viewBox="0 0 27 13" fill="none" aria-hidden>
      <rect x="0.5" y="0.5" width="22" height="12" rx="3.2" stroke="currentColor" strokeOpacity="0.45" />
      <rect x="2" y="2" width="17.5" height="9" rx="2" fill="currentColor" />
      <path
        d="M24 4.6c.8.45.8 1.35 0 1.8-.25.15-.55.22-.85.22v-2.24c.3 0 .6.07.85.22Z"
        fill="currentColor"
        fillOpacity="0.45"
      />
    </svg>
  );
}

type Props = {
  time?: string;
  light?: boolean;
};

export default function IPhoneStatusBar({ time = "9:41", light = true }: Props) {
  const tone = light ? "text-white" : "text-[#1A1A1A]";

  return (
    <div className={`pointer-events-none absolute inset-x-0 top-0 z-40 px-7 pt-[13px] ${tone}`}>
      <div className="flex items-center justify-between">
        <span className="w-[54px] text-[17px] font-semibold leading-none tracking-[-0.02em]">{time}</span>

        <div className="flex w-[74px] items-center justify-end gap-[5px] overflow-visible">
          <IosCellular />
          <span className="flex items-center pt-px">
            <IosWifi />
          </span>
          <IosBattery />
        </div>
      </div>
    </div>
  );
}
