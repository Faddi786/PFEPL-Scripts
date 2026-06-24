import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F7F7F5] p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
        <h1 className="text-xl font-semibold text-[#1A1A1A]">Page not found</h1>
        <p className="mt-2 text-sm text-slate-500">The requested route is not available in this minister demo build.</p>
        <Link
          to="/app"
          className="mt-4 inline-flex rounded-full bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-white"
        >
          Go to Workbench
        </Link>
      </div>
    </div>
  );
}
