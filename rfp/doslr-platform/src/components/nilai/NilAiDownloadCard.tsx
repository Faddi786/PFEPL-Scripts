import { FileSpreadsheet, FileText } from "lucide-react";
import { openNilAiFile, type NilAiAttachment } from "../../lib/nilAiExport";

type Props = {
  attachment: NilAiAttachment;
};

function FileIcon({ kind }: { kind: NilAiAttachment["kind"] }) {
  if (kind === "pdf") return <FileText className="h-5 w-5 text-slate-500" />;
  return <FileSpreadsheet className="h-5 w-5 text-slate-500" />;
}

export default function NilAiDownloadCard({ attachment }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50">
          <FileIcon kind={attachment.kind} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-[13px] font-semibold text-slate-900">{attachment.title}</p>
          <p className="text-[11px] text-slate-500">{attachment.subtitle}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={() => openNilAiFile(attachment.url)}
        className="shrink-0 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
      >
        Open
      </button>
    </div>
  );
}
