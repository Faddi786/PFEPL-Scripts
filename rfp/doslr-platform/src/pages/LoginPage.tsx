import { useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Landmark, Lock, UserRound } from "lucide-react";
import { loginSession } from "../lib/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [userId, setUserId] = useState("minister.demo");
  const [password, setPassword] = useState("password");

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginSession(userId || "demo.user");
    const next = (location.state as { from?: string } | null)?.from;
    navigate(next ?? "/app", { replace: true });
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F7F7F5] px-4 py-8 text-[#1A1A1A]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(56,189,248,0.12),transparent_35%),radial-gradient(circle_at_85%_15%,rgba(99,102,241,0.08),transparent_32%),linear-gradient(to_bottom,rgba(255,255,255,0.95),rgba(247,247,245,0.9))]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.03)_1px,transparent_1px)] bg-[size:34px_34px]" />

      <div className="relative w-full max-w-md rounded-3xl border border-white/70 bg-white/75 p-8 shadow-[0_18px_45px_rgba(17,24,39,0.12)] backdrop-blur-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-2xl bg-[#1A1A1A] p-2.5 text-white">
            <Landmark className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">DoSLR WebGIS</h1>
            <p className="text-xs text-slate-500">Minister Demonstration Portal</p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-slate-600">User ID</span>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
              <UserRound className="h-4 w-4 text-slate-400" />
              <input
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                className="h-11 w-full bg-transparent text-sm outline-none"
                placeholder="enter any user id"
              />
            </div>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-slate-600">Password</span>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
              <Lock className="h-4 w-4 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="h-11 w-full bg-transparent text-sm outline-none"
                placeholder="any password works"
              />
            </div>
          </label>

          <button
            type="submit"
            className="mt-1 w-full rounded-full bg-[#1A1A1A] py-2.5 text-sm font-medium text-white transition hover:bg-black"
          >
            Enter Workbench
          </button>
        </form>
      </div>
    </div>
  );
}
