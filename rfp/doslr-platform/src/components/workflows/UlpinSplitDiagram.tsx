import { ArrowDown, GitBranch } from "lucide-react";

type Props = {
  parentUlpin: string;
  childUlpins: [string, string];
};

export default function UlpinSplitDiagram({ parentUlpin, childUlpins }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-4">
      <div className="flex items-center gap-2">
        <GitBranch className="h-3.5 w-3.5 text-sky-600" />
        <p className="text-xs font-semibold text-slate-700">ULPIN generation after split</p>
      </div>
      <p className="mt-1 text-[11px] text-slate-500">One parent parcel ULIPN branches into two new records.</p>

      <div className="mt-4 flex flex-col items-center">
        <div className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-center shadow-sm">
          <p className="text-[10px] uppercase tracking-wide text-slate-400">Parent ULIPN</p>
          <p className="mt-0.5 font-mono text-xs font-semibold text-slate-800">{parentUlpin}</p>
        </div>

        <ArrowDown className="my-2 h-4 w-4 text-slate-400" />

        <div className="relative flex w-full max-w-sm items-start justify-center gap-3">
          <div className="absolute top-0 h-px w-[calc(100%-2rem)] translate-y-0 border-t border-dashed border-slate-300" />
          <div className="flex flex-1 flex-col items-center pt-3">
            <div className="h-4 w-px bg-slate-300" />
            <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-center">
              <p className="text-[10px] uppercase tracking-wide text-sky-600">New ULIPN 1</p>
              <p className="mt-0.5 font-mono text-[11px] font-semibold text-sky-900">{childUlpins[0]}</p>
            </div>
          </div>
          <div className="flex flex-1 flex-col items-center pt-3">
            <div className="h-4 w-px bg-slate-300" />
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-center">
              <p className="text-[10px] uppercase tracking-wide text-emerald-600">New ULIPN 2</p>
              <p className="mt-0.5 font-mono text-[11px] font-semibold text-emerald-900">{childUlpins[1]}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
