import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown } from "lucide-react";

export type FilterOption = { id: string; label: string };

type Props = {
  label: string;
  options: FilterOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
};

export default function ReportFilterDropdown({ label, options, selected, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState<React.CSSProperties>({});
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const allSelected = selected.length === options.length;
  const summary =
    selected.length === 0
      ? "None"
      : allSelected
        ? "All"
        : selected.length <= 2
          ? options
              .filter((opt) => selected.includes(opt.id))
              .map((opt) => opt.label)
              .join(", ")
          : `${selected.length} selected`;

  const updatePosition = useCallback(() => {
    const button = buttonRef.current;
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const menuHeight = menuRef.current?.offsetHeight ?? options.length * 32 + 48;
    const spaceBelow = window.innerHeight - rect.bottom;
    const openUp = spaceBelow < menuHeight + 8 && rect.top > spaceBelow;

    setMenuStyle({
      position: "fixed",
      left: rect.left,
      width: rect.width,
      top: openUp ? rect.top - menuHeight - 4 : rect.bottom + 4,
      zIndex: 9999,
    });
  }, [options.length]);

  useEffect(() => {
    if (!open) return;

    updatePosition();
    const raf = requestAnimationFrame(updatePosition);
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    function onDocClick(event: MouseEvent) {
      const target = event.target as Node;
      if (!rootRef.current?.contains(target) && !menuRef.current?.contains(target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
      document.removeEventListener("mousedown", onDocClick);
    };
  }, [open, updatePosition]);

  function toggleOption(id: string) {
    if (selected.includes(id)) {
      onChange(selected.filter((item) => item !== id));
      return;
    }
    onChange([...selected, id]);
  }

  function toggleAll() {
    if (allSelected) {
      onChange([]);
      return;
    }
    onChange(options.map((opt) => opt.id));
  }

  const menu = open ? (
    <div
      ref={menuRef}
      style={menuStyle}
      className="max-h-[280px] overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg"
    >
      <button
        type="button"
        onClick={toggleAll}
        className="sticky top-0 z-10 flex w-full items-center justify-between border-b border-slate-100 bg-slate-50 px-2.5 py-2 text-left text-[11px] font-semibold text-slate-700"
      >
        <span>{allSelected ? "Deselect all" : "Select all"}</span>
        {allSelected ? <Check className="h-3.5 w-3.5" /> : null}
      </button>
      {options.map((option) => {
        const active = selected.includes(option.id);
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => toggleOption(option.id)}
            className={`flex w-full items-center justify-between px-2.5 py-2 text-left text-xs transition ${
              active ? "bg-[#1A1A1A] text-white" : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            <span>{option.label}</span>
            {active ? <Check className="h-3.5 w-3.5" /> : null}
          </button>
        );
      })}
    </div>
  ) : null;

  return (
    <div ref={rootRef} className="relative">
      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</span>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`flex w-full items-center gap-2 rounded-xl border bg-white px-2.5 py-2.5 text-left text-sm transition hover:border-slate-300 ${
          open ? "border-[#1A1A1A]" : "border-slate-200"
        }`}
      >
        <span className="min-w-0 flex-1 truncate text-slate-800">{summary}</span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-slate-400 transition ${open ? "rotate-180" : ""}`} />
      </button>
      {menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
