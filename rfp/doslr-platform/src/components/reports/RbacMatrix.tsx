import { Check, X } from "lucide-react";
import type { RbacRole } from "../../data/reports";

type Props = {
  functions: string[];
  roles: RbacRole[];
};

export default function RbacMatrix({ functions, roles }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-4 py-3">
        <p className="text-sm font-semibold text-[#1A1A1A]">Role × Function access matrix</p>
        <p className="text-xs text-slate-500">Green = permitted · Red = denied · User counts per role</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/80">
              <th className="sticky left-0 z-10 bg-slate-50/95 px-4 py-3 font-semibold text-slate-700">Role</th>
              <th className="px-3 py-3 font-semibold text-slate-500">Users</th>
              {functions.map((fn) => (
                <th key={fn} className="min-w-[108px] px-2 py-3 text-center font-medium text-slate-500">
                  <span className="block max-w-[96px] truncate" title={fn}>
                    {fn}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.role} className="border-b border-slate-50 hover:bg-slate-50/60">
                <td className="sticky left-0 z-10 bg-white px-4 py-3">
                  <p className="font-semibold text-slate-800">{role.role}</p>
                  <p className="mt-0.5 max-w-[200px] text-[11px] text-slate-500">{role.description}</p>
                </td>
                <td className="px-3 py-3 font-medium text-slate-700">{role.users.toLocaleString()}</td>
                {functions.map((fn) => {
                  const allowed = role.permissions[fn];
                  return (
                    <td key={fn} className="px-2 py-3 text-center">
                      <span
                        className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${
                          allowed ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-500"
                        }`}
                      >
                        {allowed ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
