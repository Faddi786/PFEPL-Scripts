import { useMemo, useState } from "react";
import { BarChart3, ChevronRight, Layers, Route, Smartphone, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import CollapsiblePanel from "../components/CollapsiblePanel";
import LayerPanel from "../components/LayerPanel";
import MapView from "../components/MapView";
import WorkflowPanel from "../components/WorkflowPanel";
import { getLayerGroups, type LayerGroup, type RegionKey } from "../data/mockData";

export default function MapWorkbenchPage() {
  const initialLayers = useMemo(() => getLayerGroups(), []);
  const [region, setRegion] = useState<RegionKey>("puducherry");
  const [layerGroups, setLayerGroups] = useState<LayerGroup[]>(initialLayers);
  const [activeBasemap, setActiveBasemap] = useState("basemap-carto");
  const [layersOpen, setLayersOpen] = useState(false);
  const [workflowsOpen, setWorkflowsOpen] = useState(false);

  function toggleLayer(layerId: string, visible: boolean) {
    setLayerGroups((prev) =>
      prev.map((group) => ({
        ...group,
        layers: group.layers.map((layer) => (layer.id === layerId ? { ...layer, visible } : layer)),
      })),
    );
  }

  function setBasemap(id: string) {
    setActiveBasemap(id);
    setLayerGroups((prev) =>
      prev.map((group) => ({
        ...group,
        layers: group.layers.map((layer) =>
          layer.id.startsWith("basemap-") ? { ...layer, visible: layer.id === id } : layer,
        ),
      })),
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F7F5] p-3 text-[#1A1A1A] lg:p-4">
      <div className="mx-auto grid h-full w-full max-w-[1700px] min-h-0 gap-3 lg:grid-cols-[minmax(0,1fr)_340px]">
        <MapView
          regionKey={region}
          layerGroups={layerGroups}
          basemapId={activeBasemap}
        />

        <aside className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-white/70 bg-white/85 shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
              <CollapsiblePanel
                title="Layers"
                icon={<Layers className="h-4 w-4" />}
                open={layersOpen}
                onToggle={() => setLayersOpen((v) => !v)}
              >
                <LayerPanel
                  layerGroups={layerGroups}
                  onBasemapChange={setBasemap}
                  activeRegion={region}
                  onRegionChange={setRegion}
                  onToggleLayer={toggleLayer}
                />
              </CollapsiblePanel>

              <CollapsiblePanel
                title="Workflows"
                icon={<Route className="h-4 w-4" />}
                open={workflowsOpen}
                onToggle={() => setWorkflowsOpen((v) => !v)}
              >
                <WorkflowPanel />
              </CollapsiblePanel>

              <Link
                to="/reports"
                className="group flex w-full items-center justify-between rounded-2xl border border-white/70 bg-white/85 px-4 py-3 shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition hover:border-slate-200 hover:bg-white"
              >
                <span className="flex items-center gap-2 text-sm font-semibold text-[#1A1A1A]">
                  <BarChart3 className="h-4 w-4 text-slate-600" />
                  Reports
                </span>
                <ChevronRight className="h-4 w-4 text-slate-400 transition group-hover:text-slate-700" />
              </Link>

              <Link
                to="/mobile"
                className="group flex w-full items-center justify-between rounded-2xl border border-white/70 bg-white/85 px-4 py-3 shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition hover:border-slate-200 hover:bg-white"
              >
                <span className="flex items-center gap-2 text-sm font-semibold text-[#1A1A1A]">
                  <Smartphone className="h-4 w-4 text-slate-600" />
                  Nilam Mobile
                </span>
                <ChevronRight className="h-4 w-4 text-slate-400 transition group-hover:text-slate-700" />
              </Link>

              <Link
                to="/nil-ai"
                className="group flex w-full items-center justify-between rounded-2xl border border-white/70 bg-white/85 px-4 py-3 shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition hover:border-slate-200 hover:bg-white"
              >
                <span className="flex items-center gap-2 text-sm font-semibold text-[#1A1A1A]">
                  <Sparkles className="h-4 w-4 text-slate-600" />
                  NIL-AI
                </span>
                <ChevronRight className="h-4 w-4 text-slate-400 transition group-hover:text-slate-700" />
              </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
