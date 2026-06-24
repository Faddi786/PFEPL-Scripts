import { useCallback, useState, type FormEvent } from "react";
import { Landmark, Lock, ShieldCheck, UserRound } from "lucide-react";
import { useMobileApp } from "../MobileAppContext";
import MobileAuthSuccessOverlay from "./MobileAuthSuccessOverlay";

const DEMO_OTP = "4721";

export default function MobileLoginScreen() {
  const { login, pushIslandNotification } = useMobileApp();
  const [userId, setUserId] = useState("surveyor.py.1042");
  const [password, setPassword] = useState("password");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState("");
  const [authenticating, setAuthenticating] = useState(false);

  const finishAuthAnimation = useCallback(() => {
    login(userId);
    setAuthenticating(false);
  }, [login, userId]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (!otpSent) {
      setOtpSent(true);
      pushIslandNotification({
        title: "DoSLR Nilam",
        subtitle: `Your OTP is ${DEMO_OTP}`,
        icon: "message",
        durationMs: 3000,
      });
      return;
    }

    if (otp.trim() !== DEMO_OTP) {
      setError("Invalid OTP");
      return;
    }

    setAuthenticating(true);
  }

  return (
    <div className="relative flex h-full flex-col overflow-y-auto px-5 pb-6 pt-2">
      {authenticating ? <MobileAuthSuccessOverlay onComplete={finishAuthAnimation} /> : null}
      <div className="mb-6 mt-4 text-center">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1A1A1A] text-white">
          <Landmark className="h-7 w-7" />
        </div>
        <h1 className="text-lg font-semibold text-[#1A1A1A]">Nilam Mobile</h1>
        <p className="mt-1 text-xs text-slate-500">Field Integration · DoSLR Puducherry</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Officer ID
          </span>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
            <UserRound className="h-4 w-4 text-slate-400" />
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="h-10 w-full bg-transparent text-sm outline-none"
            />
          </div>
        </label>

        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Password
          </span>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
            <Lock className="h-4 w-4 text-slate-400" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10 w-full bg-transparent text-sm outline-none"
            />
          </div>
        </label>

        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            OTP
          </span>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
            <ShieldCheck className="h-4 w-4 text-slate-400" />
            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 4))}
              placeholder={otpSent ? "Enter 4-digit OTP" : "OTP after Send OTP"}
              className="h-10 w-full bg-transparent text-sm outline-none"
              inputMode="numeric"
            />
          </div>
        </label>

        {error ? <p className="text-xs text-rose-600">{error}</p> : null}

        <button
          type="submit"
          disabled={authenticating}
          className="mt-2 w-full rounded-full bg-[#1A1A1A] py-2.5 text-sm font-medium text-white disabled:bg-slate-400"
        >
          {otpSent ? "Sign in" : "Send OTP"}
        </button>
      </form>
    </div>
  );
}
