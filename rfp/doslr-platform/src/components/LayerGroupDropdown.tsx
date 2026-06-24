import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown } from "lucide-react";
import type { LayerConfig } from "../data/mockData";

type Props = {
  label: string;
  layers: LayerConfig[];
  onToggle: (layerId: string, visible: boolean) => void;
  single?: boolean;
  /** Basemap only: hover an open menu item to preview without clicking */
  hoverPreview?: boolean;
};

export default function LayerGroupDropdown({
  label,
  layers,
  onToggle,
  single = false,
  hoverPreview = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState<React.CSSProperties>({});
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const active = layers.filter((layer) => layer.visible);
  const summary = active.length === 0 ? "None" : `${active.length} active`;

  const updatePosition = useCallback(() => {
    const button = buttonRef.current;
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const menuHeight = menuRef.current?.offsetHeight ?? layers.length * 36 + 8;
    const spaceBelow = window.innerHeight - rect.bottom;
    const openUp = spaceBelow < menuHeight + 8 && rect.top > spaceBelow;

    setMenuStyle({
      position: "fixed",
      left: rect.left,
      width: rect.width,
      top: openUp ? rect.top - menuHeight - 4 : rect.bottom + 4,
      zIndex: 9999,
    });
  }, [layers.length]);

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

  function handlePick(layer: LayerConfig) {
    if (single) {
      layers.forEach((item) => onToggle(item.id, item.id === layer.id));
      setOpen(false);
      return;
    }
    onToggle(layer.id, !layer.visible);
  }

  function handleHover(layer: LayerConfig) {
    if (!hoverPreview || !single || layer.visible) return;
    layers.forEach((item) => onToggle(item.id, item.id === layer.id));
  }

  const menu = open ? (
    <div
      ref={menuRef}
      style={menuStyle}
      className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
    >
      {layers.map((layer) => {
        const selected = layer.visible;
        return (
          <button
            key={layer.id}
            type="button"
            onMouseEnter={hoverPreview ? () => handleHover(layer) : undefined}
            onClick={() => handlePick(layer)}
            className={`flex w-full items-center justify-between px-2.5 py-2 text-left text-xs transition ${
              selected ? "bg-[#1A1A1A] text-white" : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            <span>{layer.label}</span>
            {selected ? <Check className="h-3.5 w-3.5" /> : null}
          </button>
        );
      })}
    </div>
  ) : null;

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`flex w-full items-center gap-2 rounded-lg border bg-white px-2.5 py-2 text-left text-xs transition hover:border-slate-300 ${
          open ? "border-[#1A1A1A]" : "border-slate-200"
        }`}
      >
        <span className="shrink-0 font-medium text-slate-800">{label}</span>
        <span className="min-w-0 flex-1 truncate text-right text-slate-500">{summary}</span>
        <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition ${open ? "rotate-180" : ""}`} />
      </button>

      {menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
