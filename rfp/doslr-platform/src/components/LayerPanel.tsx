import LayerGroupDropdown from "./LayerGroupDropdown";
import type { LayerConfig, LayerGroup, RegionKey } from "../data/mockData";

type Props = {
  layerGroups: LayerGroup[];
  onBasemapChange: (id: string) => void;
  activeRegion: RegionKey;
  onRegionChange: (region: RegionKey) => void;
  onToggleLayer: (layerId: string, visible: boolean) => void;
};

const regionOptions: { key: RegionKey; label: string }[] = [
  { key: "puducherry", label: "Puducherry" },
  { key: "karaikal", label: "Karaikal" },
  { key: "mahe", label: "Mahe" },
  { key: "yanam", label: "Yanam" },
];

export default function LayerPanel({
  layerGroups,
  onBasemapChange,
  activeRegion,
  onRegionChange,
  onToggleLayer,
}: Props) {
  const basemapGroup = layerGroups.find((group) => group.id === "basemap");
  const overlayGroups = layerGroups.filter((group) => group.id !== "basemap");

  const regionLayers: LayerConfig[] = regionOptions.map((option) => ({
    id: option.key,
    label: option.label,
    visible: option.key === activeRegion,
  }));

  return (
    <div className="space-y-1.5">
      {basemapGroup ? (
        <LayerGroupDropdown
          label="Basemap"
          layers={basemapGroup.layers}
          single
          hoverPreview
          onToggle={(id, visible) => {
            if (visible) onBasemapChange(id);
          }}
        />
      ) : null}

      <LayerGroupDropdown
        label="Region"
        layers={regionLayers}
        single
        onToggle={(id, visible) => {
          if (visible) onRegionChange(id as RegionKey);
        }}
      />

      {overlayGroups.map((group) => (
        <LayerGroupDropdown
          key={group.id}
          label={group.label}
          layers={group.layers}
          onToggle={onToggleLayer}
        />
      ))}
    </div>
  );
}
