import { LogOut, MapPinned, UserCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getAuthUser, logoutSession } from "../lib/auth";

type Props = {
  title?: string;
};

export default function HeaderBar({ title = "DoSLR WebGIS Minister Demo" }: Props) {
  const navigate = useNavigate();
  const user = getAuthUser();

  return (
    <header className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/80 px-5 py-3 shadow-[0_8px_30px_rgba(0,0,0,0.06)] backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-[#1A1A1A] p-2 text-white">
          <MapPinned className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-wide text-[#1A1A1A]">{title}</h1>
          <p className="text-xs text-slate-500">Digital land records workbench for Puducherry UT</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">Minister View</span>
        <div className="flex items-center gap-2 rounded-full bg-slate-100/70 px-3 py-1.5">
          <UserCircle2 className="h-4 w-4 text-slate-600" />
          <span className="text-xs font-medium text-slate-700">{user?.userId ?? "demo.user"}</span>
        </div>
        <button
          type="button"
          onClick={() => {
            logoutSession();
            navigate("/login", { replace: true });
          }}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
        >
          <LogOut className="h-3.5 w-3.5" />
          Logout
        </button>
      </div>
    </header>
  );
}
