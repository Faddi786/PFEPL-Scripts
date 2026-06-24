import { Fill, Stroke, Style, Text } from "ol/style";
import type { FeatureLike } from "ol/Feature";

export type ParcelMapVariant = "default" | "edit" | "before" | "after";

const variantStyles: Record<ParcelMapVariant, { stroke: string; fill: string; width: number }> = {
  default: { stroke: "#0f172a", fill: "rgba(148,163,184,0.35)", width: 1.1 },
  edit: { stroke: "#2563eb", fill: "rgba(59,130,246,0.18)", width: 2.2 },
  before: { stroke: "#64748b", fill: "rgba(148,163,184,0.42)", width: 1.4 },
  after: { stroke: "#0ea5e9", fill: "rgba(14,165,233,0.28)", width: 1.6 },
};

const PIECE_SUFFIXES = ["A", "B"] as const;

export function parcelLabelText(
  surveyNo: string,
  pieceIndex: number | undefined,
  isSplit: boolean,
): string {
  if (!isSplit || pieceIndex === undefined) return surveyNo;
  const suffix = PIECE_SUFFIXES[pieceIndex];
  return suffix ? `${surveyNo}${suffix}` : surveyNo;
}

export function createParcelStyle(
  variant: ParcelMapVariant,
  surveyNo?: string,
  isSplit = false,
) {
  const colors = variantStyles[variant];
  return (feature: FeatureLike, resolution: number) => {
    if (feature.getGeometry()?.getType() !== "Polygon") {
      return new Style({
        stroke: new Stroke({ color: colors.stroke, width: colors.width }),
        fill: new Fill({ color: colors.fill }),
      });
    }

    const pieceIndex = feature.get("pieceIndex") as number | undefined;
    const label =
      surveyNo && resolution < 5
        ? parcelLabelText(surveyNo, pieceIndex, isSplit)
        : undefined;

    return new Style({
      stroke: new Stroke({ color: colors.stroke, width: colors.width }),
      fill: new Fill({ color: colors.fill }),
      text: label
        ? new Text({
            text: label,
            font: "600 10px ui-monospace,Consolas,monospace",
            fill: new Fill({ color: "#111" }),
            stroke: new Stroke({ color: "#fff", width: 2 }),
            overflow: true,
          })
        : undefined,
    });
  };
}
