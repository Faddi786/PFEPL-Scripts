import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import Map from "ol/Map";
import View from "ol/View";
import { defaults as defaultControls } from "ol/control";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import Draw from "ol/interaction/Draw";
import type Feature from "ol/Feature";
import type { Geometry } from "ol/geom";
import { Stroke, Style } from "ol/style";
import { createParcelStyle, type ParcelMapVariant } from "../../lib/parcelMapStyles";
import { extendCutLineAcrossPolygon, splitPolygonByLine } from "../../lib/splitPolygon";

export type MutationMapGeometry =
  | GeoJSON.Feature<GeoJSON.Polygon>
  | GeoJSON.FeatureCollection<GeoJSON.Polygon>;

export type MutationEditMapHandle = {
  getGeometry: () => MutationMapGeometry | null;
  isSplit: () => boolean;
};

type Props = {
  parcel: MutationMapGeometry;
  editable?: boolean;
  tool?: "split" | "view";
  variant?: ParcelMapVariant;
  className?: string;
  onReady?: (geometry: GeoJSON.Feature<GeoJSON.Polygon>) => void;
  onSplit?: (pieces: GeoJSON.Feature<GeoJSON.Polygon>[]) => void;
};

function toFeatures(parcel: MutationMapGeometry): GeoJSON.Feature<GeoJSON.Polygon>[] {
  if (parcel.type === "FeatureCollection") return parcel.features;
  return [parcel];
}

const MutationEditMap = forwardRef<MutationEditMapHandle, Props>(function MutationEditMap(
  { parcel, editable = false, tool = "view", variant = "default", className, onReady, onSplit },
  ref,
) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const parcelSourceRef = useRef<VectorSource | null>(null);
  const splitDoneRef = useRef(false);
  const formatRef = useRef(new GeoJSON());
  const onReadyRef = useRef(onReady);
  const onSplitRef = useRef(onSplit);
  const readySentRef = useRef(false);
  const originalParcelRef = useRef<GeoJSON.Feature<GeoJSON.Polygon> | null>(null);

  onReadyRef.current = onReady;
  onSplitRef.current = onSplit;

  useImperativeHandle(ref, () => ({
    getGeometry: () => {
      const source = parcelSourceRef.current;
      if (!source) return null;
      const features = source.getFeatures();
      if (features.length === 0) return null;
      if (features.length === 1) {
        return formatRef.current.writeFeatureObject(features[0], {
          featureProjection: "EPSG:3857",
          dataProjection: "EPSG:4326",
        }) as GeoJSON.Feature<GeoJSON.Polygon>;
      }
      return {
        type: "FeatureCollection",
        features: features.map(
          (feature) =>
            formatRef.current.writeFeatureObject(feature, {
              featureProjection: "EPSG:3857",
              dataProjection: "EPSG:4326",
            }) as GeoJSON.Feature<GeoJSON.Polygon>,
        ),
      };
    },
    isSplit: () => splitDoneRef.current,
  }));

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const format = formatRef.current;
    const inputFeatures = toFeatures(parcel);
    const parcelSource = new VectorSource();
    inputFeatures.forEach((item, index) => {
      const olFeature = format.readFeature(item, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }) as Feature<Geometry>;
      olFeature.set("pieceIndex", index);
      parcelSource.addFeature(olFeature);
    });
    parcelSourceRef.current = parcelSource;
    splitDoneRef.current = inputFeatures.length > 1;

    const first = inputFeatures[0];
    originalParcelRef.current = first;
    const surveyNo = String(first.properties?.surveyNo ?? "");

    const basemap = new TileLayer({
      source: new XYZ({
        url: "https://{a-d}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        attributions: "&copy; OpenStreetMap contributors &copy; CARTO",
      }),
    });

    const parcelLayer = new VectorLayer({
      source: parcelSource,
      zIndex: 2,
      style: (feature, resolution) => {
        const pieceIndex = feature.get("pieceIndex") as number | undefined;
        const pieceVariant =
          pieceIndex === 1 ? "after" : pieceIndex === 0 && splitDoneRef.current ? "before" : variant;
        return createParcelStyle(pieceVariant, surveyNo, splitDoneRef.current)(feature, resolution);
      },
    });

    const map = new Map({
      target: containerRef.current,
      controls: defaultControls({ zoom: true, attribution: false }),
      layers: [basemap, parcelLayer],
      view: new View({ zoom: 18 }),
    });

    const extent = parcelSource.getExtent();
    if (extent && extent.every((value) => Number.isFinite(value))) {
      map.getView().fit(extent, { padding: [24, 24, 24, 24], duration: 0, maxZoom: 19 });
    }

    mapRef.current = map;

    if (!readySentRef.current && first) {
      readySentRef.current = true;
      onReadyRef.current?.(first);
    }

    const resize = () => map.updateSize();
    requestAnimationFrame(resize);
    const observer = new ResizeObserver(resize);
    observer.observe(containerRef.current);
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      observer.disconnect();
      map.setTarget(undefined);
      mapRef.current = null;
      parcelSourceRef.current = null;
      readySentRef.current = false;
      splitDoneRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const layer = map.getLayers().item(1) as VectorLayer<VectorSource>;
    const surveyNo = String(originalParcelRef.current?.properties?.surveyNo ?? "");
    layer.setStyle((feature, resolution) => {
      const pieceIndex = feature.get("pieceIndex") as number | undefined;
      const pieceVariant =
        pieceIndex === 1 ? "after" : pieceIndex === 0 && splitDoneRef.current ? "before" : variant;
      return createParcelStyle(pieceVariant, surveyNo, splitDoneRef.current)(feature, resolution);
    });
  }, [variant]);

  useEffect(() => {
    const map = mapRef.current;
    const source = parcelSourceRef.current;
    const original = originalParcelRef.current;
    if (!map || !source || !original) return;

    const existing = map
      .getInteractions()
      .getArray()
      .filter((interaction) => interaction instanceof Draw);
    existing.forEach((interaction) => map.removeInteraction(interaction));

    if (!editable || tool !== "split" || splitDoneRef.current) return;

    const parcelLayer = map.getLayers().item(1) as VectorLayer<VectorSource>;

    const cutSource = new VectorSource();
    const cutLayer = new VectorLayer({
      source: cutSource,
      zIndex: 3,
      style: new Style({
        stroke: new Stroke({ color: "#7c3aed", width: 2.5, lineDash: [8, 6] }),
      }),
    });
    map.addLayer(cutLayer);

    const draw = new Draw({ source: cutSource, type: "LineString" });
    draw.on("drawend", (event) => {
      draw.setActive(false);
      cutSource.removeFeature(event.feature);

      const cutLine = formatRef.current.writeFeatureObject(event.feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326",
      }) as GeoJSON.Feature<GeoJSON.LineString>;

      cutSource.clear();

      const extended = extendCutLineAcrossPolygon(cutLine);
      const pieces = splitPolygonByLine(original, extended);
      if (!pieces) {
        draw.setActive(true);
        return;
      }

      source.clear();
      pieces.forEach((piece, index) => {
        const olFeature = formatRef.current.readFeature(
          {
            ...piece,
            properties: {
              ...original.properties,
              pieceIndex: index,
            },
          },
          { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" },
        ) as Feature<Geometry>;
        olFeature.set("pieceIndex", index);
        source.addFeature(olFeature);
      });

      splitDoneRef.current = true;
      cutSource.clear();
      map.removeLayer(cutLayer);
      map.removeInteraction(draw);
      parcelLayer.changed();
      const nextExtent = source.getExtent();
      if (nextExtent) {
        map.getView().fit(nextExtent, { padding: [24, 24, 24, 24], duration: 250, maxZoom: 19 });
      }
      onSplitRef.current?.(pieces);
    });

    map.addInteraction(draw);
    return () => {
      map.removeInteraction(draw);
      map.removeLayer(cutLayer);
    };
  }, [editable, tool]);

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100 ${className ?? ""}`}
    >
      <div ref={containerRef} className="h-full w-full min-h-[220px]" />
      {splitDoneRef.current ? (
        <span className="pointer-events-none absolute left-2 top-2 rounded-full bg-emerald-600/90 px-2 py-0.5 text-[10px] font-medium text-white">
          Parcel split complete
        </span>
      ) : null}
    </div>
  );
});

export default MutationEditMap;
