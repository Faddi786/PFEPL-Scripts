import { ChevronDown, Gauge, Merge, Move3d, Ruler, Scissors, Wrench } from "lucide-react";
import type { MapTool } from "../lib/mapEngine";

type ToolItem = { id: MapTool; label: string; icon: typeof Move3d };

const toolItems: ToolItem[] = [
  { id: "vertex-edit", label: "Vertex Edit", icon: Move3d },
  { id: "split", label: "Split", icon: Scissors },
  { id: "amalgamate", label: "Amalgamate", icon: Merge },
  { id: "measure-distance", label: "Measure", icon: Ruler },
  { id: "buffer", label: "Buffer", icon: Gauge },
];

const toolLabels: Record<MapTool, string> = {
  none: "Tools",
  "vertex-edit": "Vertex Edit",
  split: "Split",
  amalgamate: "Amalgamate",
  "measure-distance": "Measure",
  buffer: "Buffer",
};

type Props = {
  activeTool: MapTool;
  onSelectTool: (tool: MapTool) => void;
};

export default function MapToolsDropdown({ activeTool, onSelectTool }: Props) {
  return (
    <div className="group absolute right-4 top-4 z-20">
      <button
        type="button"
        className="flex items-center gap-2 rounded-full border border-white/80 bg-white/95 px-3 py-2 text-xs font-medium text-slate-700 shadow-lg backdrop-blur-md transition hover:border-slate-200"
      >
        <Wrench className="h-3.5 w-3.5 text-slate-600" />
        <span>{toolLabels[activeTool]}</span>
        <ChevronDown className="h-3.5 w-3.5 text-slate-500 transition group-hover:rotate-180" />
      </button>

      <div className="pointer-events-none invisible absolute right-0 top-full z-30 pt-1 opacity-0 transition-all duration-150 group-hover:pointer-events-auto group-hover:visible group-hover:opacity-100">
        <div className="min-w-[168px] overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-xl backdrop-blur-md">
          {toolItems.map((item) => {
            const Icon = item.icon;
            const active = activeTool === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTool(item.id)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition ${
                  active ? "bg-[#1A1A1A] text-white" : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
