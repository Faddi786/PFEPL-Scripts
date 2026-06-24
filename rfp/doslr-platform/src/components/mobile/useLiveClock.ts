import { useEffect, useState } from "react";

function formatTime12Hour(date: Date) {
  const hours = date.getHours() % 12 || 12;
  const minutes = date.getMinutes();
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

export function useLiveClock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const tick = () => setNow(new Date());
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  const time = formatTime12Hour(now);
  const lockTimeLarge = formatTime12Hour(now);

  const dateLine = now.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return { now, time, dateLine, lockTimeLarge };
}
