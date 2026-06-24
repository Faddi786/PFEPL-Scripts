import { useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCheck, CircleAlert, Clock3, Upload, ArrowLeft } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import WorkflowStepper from "../../components/WorkflowStepper";
import MutationEditMap, { type MutationEditMapHandle, type MutationMapGeometry } from "../../components/workflows/MutationEditMap";
import GeoreferencingMap from "../../components/workflows/GeoreferencingMap";
import AnomalyPipelineFlow from "../../components/workflows/AnomalyPipelineFlow";
import UlpinSplitDiagram from "../../components/workflows/UlpinSplitDiagram";
import { getRegionDataset } from "../../data/mockData";
import { WORKFLOW_LOOKUP, type WorkflowId } from "../../data/workflows";
import { deriveSplitUlpins } from "../../lib/splitPolygon";

function OnlineMutationFlow() {
  const steps = ["Split parcel", "Review", "Approve/Reject", "Sync to all 3 databases real time"];

  const demoParcel = useMemo(() => {
    const dataset = getRegionDataset("puducherry");
    const parcels = dataset.geojson.parcels.features as GeoJSON.Feature<GeoJSON.Polygon>[];
    const preferred =
      parcels.find((feature) => String(feature.properties?.surveyNo ?? "").includes("42")) ??
      parcels.find((feature) => (feature.geometry.coordinates[0]?.length ?? 0) >= 5) ??
      parcels[0];
    return preferred;
  }, []);

  const parcelMeta = useMemo(
    () => ({
      surveyNo: String(demoParcel.properties?.surveyNo ?? "—"),
      village: String(demoParcel.properties?.village ?? "—"),
      id: String(demoParcel.properties?.id ?? "—"),
      ulpin: String(demoParcel.properties?.ulpin ?? "—"),
    }),
    [demoParcel],
  );

  const childUlpins = useMemo(
    () => deriveSplitUlpins(parcelMeta.ulpin),
    [parcelMeta.ulpin],
  );

  const editMapRef = useRef<MutationEditMapHandle>(null);
  const [step, setStep] = useState(0);
  const [beforeGeometry, setBeforeGeometry] = useState<GeoJSON.Feature<GeoJSON.Polygon> | null>(null);
  const [afterGeometry, setAfterGeometry] = useState<MutationMapGeometry | null>(null);
  const [reviewMode, setReviewMode] = useState<"before" | "after">("before");
  const [splitDone, setSplitDone] = useState(false);
  const [decision, setDecision] = useState<"pending" | "approved" | "rejected">("pending");
  const [showRejectPanel, setShowRejectPanel] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [synced, setSynced] = useState(false);

  const isSplitting = step === 0;
  const showReview = step >= 1;
  const showDecision = step >= 1 && decision === "pending";

  function handleMapReady(geometry: GeoJSON.Feature<GeoJSON.Polygon>) {
    setBeforeGeometry((current) => current ?? geometry);
  }

  function handleSplit(pieces: GeoJSON.Feature<GeoJSON.Polygon>[]) {
    setSplitDone(true);
    setAfterGeometry({
      type: "FeatureCollection",
      features: pieces.map((piece, index) => ({
        ...piece,
        properties: { ...demoParcel.properties, pieceIndex: index },
      })),
    });
  }

  function submitMutation() {
    if (!editMapRef.current?.isSplit()) return;
    const geometry = editMapRef.current.getGeometry();
    if (!geometry) return;
    setAfterGeometry(geometry);
    setStep(1);
    setReviewMode("after");
  }

  function approveMutation() {
    setDecision("approved");
    setStep(steps.length);
    setSyncing(true);
    window.setTimeout(() => {
      setSyncing(false);
      setSynced(true);
    }, 1400);
  }

  function rejectMutation() {
    if (!rejectReason.trim()) return;
    setDecision("rejected");
    setShowRejectPanel(false);
    setStep(steps.length);
  }

  const reviewGeometry: MutationMapGeometry | null =
    reviewMode === "before"
      ? beforeGeometry
      : afterGeometry ?? beforeGeometry;

  return (
    <div className="space-y-4">
      <WorkflowStepper steps={steps} activeStep={step} />

      <div className="grid gap-4 xl:grid-cols-[1.15fr_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-[#1A1A1A]">
            {isSplitting ? "Officer: split parcel" : "Submitted split geometry"}
          </h3>

          <div className="mt-3 h-[min(52vh,420px)]">
            {isSplitting ? (
              <MutationEditMap
                ref={editMapRef}
                parcel={demoParcel}
                editable
                tool="split"
                variant="edit"
                className="h-full"
                onReady={handleMapReady}
                onSplit={handleSplit}
              />
            ) : afterGeometry ? (
              <MutationEditMap
                key="submitted-after"
                parcel={afterGeometry}
                editable={false}
                tool="view"
                variant="after"
                className="h-full"
              />
            ) : null}
          </div>

          {isSplitting ? (
            <div className="mt-3">
              <button
                type="button"
                onClick={submitMutation}
                disabled={!splitDone}
                className="rounded-full bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-white disabled:opacity-40"
              >
                Submit mutation
              </button>
            </div>
          ) : (
            <div className="mt-3 rounded-xl border border-sky-100 bg-sky-50 p-3 text-xs text-sky-800">
              Mutation submitted for review. Compare before and after in the review panel.
            </div>
          )}
        </section>

        <AnimatePresence initial={false}>
          {showReview && beforeGeometry && reviewGeometry ? (
            <motion.section
              key="review-panel"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.32, ease: "easeOut" }}
              className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-[#1A1A1A]">Review: before / after</h3>
                <div className="inline-flex rounded-full border border-slate-200 bg-slate-50 p-0.5">
                  <button
                    type="button"
                    onClick={() => setReviewMode("before")}
                    className={`rounded-full px-3 py-1 text-[11px] font-medium ${
                      reviewMode === "before" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"
                    }`}
                  >
                    Before
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewMode("after")}
                    className={`rounded-full px-3 py-1 text-[11px] font-medium ${
                      reviewMode === "after" ? "bg-white text-sky-700 shadow-sm" : "text-slate-500"
                    }`}
                  >
                    After
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-500">
                {reviewMode === "before"
                  ? "Original parcel boundary captured when splitting started."
                  : "Proposed boundaries after officer split."}
              </p>

              <MutationEditMap
                key={`review-${reviewMode}`}
                parcel={reviewGeometry}
                editable={false}
                tool="view"
                variant={reviewMode}
                className="h-52"
              />

              <UlpinSplitDiagram parentUlpin={parcelMeta.ulpin} childUlpins={childUlpins} />

              {showDecision ? (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.28, ease: "easeOut" }}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                >
                  <p className="text-sm font-semibold text-[#1A1A1A]">Approve / Reject</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={approveMutation}
                      className="rounded-full bg-emerald-600 px-4 py-2 text-xs font-medium text-white"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowRejectPanel(true)}
                      className="rounded-full bg-rose-600 px-4 py-2 text-xs font-medium text-white"
                    >
                      Reject
                    </button>
                  </div>

                  {showRejectPanel ? (
                    <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3">
                      <p className="text-xs font-semibold text-rose-700">Rejection reason required</p>
                      <textarea
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        className="mt-2 h-20 w-full rounded-lg border border-rose-200 bg-white p-2 text-xs outline-none"
                        placeholder="Enter reason for rejection..."
                      />
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={rejectMutation}
                          disabled={!rejectReason.trim()}
                          className="rounded-full bg-rose-700 px-3 py-1.5 text-xs text-white disabled:opacity-40"
                        >
                          Confirm reject
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowRejectPanel(false)}
                          className="rounded-full border border-rose-200 bg-white px-3 py-1.5 text-xs text-rose-700"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : null}
                </motion.div>
              ) : null}

              {syncing ? (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-xl border border-sky-200 bg-sky-50 p-3 text-xs text-sky-800"
                >
                  <p className="font-semibold">Syncing to all 3 databases in real time…</p>
                  <p className="mt-1 text-sky-700">Pushing cadastral ledger, registry mirror, and mobile field cache.</p>
                </motion.div>
              ) : null}

              {synced ? (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.28, ease: "easeOut" }}
                  className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700"
                >
                  <p className="font-semibold">Synced to all 3 databases in real time.</p>
                  <p className="mt-1">Cadastral ledger, registry mirror, and mobile field cache acknowledged transaction DOSLR-2026-44291.</p>
                </motion.div>
              ) : null}

              {decision === "rejected" ? (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                  Mutation rejected. Reason: {rejectReason}
                </div>
              ) : null}
            </motion.section>
          ) : (
            <motion.section
              key="split-hint"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-dashed border-slate-200 bg-white/70 p-4"
            >
              <h3 className="text-sm font-semibold text-[#1A1A1A]">Review panel</h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-500">
                Split the parcel on the map, then submit to reveal before/after review and approve or reject controls.
              </p>
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function GeoreferencingFlow() {
  const steps = ["Upload data", "Adjust DGPS points", "Accept"];
  const [step, setStep] = useState(0);
  const [dgpsLoaded, setDgpsLoaded] = useState(false);
  const [pointsAdjusted, setPointsAdjusted] = useState(false);
  const [accepted, setAccepted] = useState(false);

  function uploadData() {
    setDgpsLoaded(true);
    setStep(1);
  }

  function acceptGeoref() {
    setAccepted(true);
    setStep(steps.length);
  }

  return (
    <div className="space-y-4">
      <WorkflowStepper steps={steps} activeStep={step} />

      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-[#1A1A1A]">Georeferencing workspace</h3>
          {dgpsLoaded ? (
            <span className="rounded-full bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-800">
              {pointsAdjusted ? "GCPs adjusted" : "6 DGPS points loaded"}
            </span>
          ) : (
            <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-600">Map ready</span>
          )}
        </div>

        <div className="mt-3 h-[min(58vh,480px)]">
          <GeoreferencingMap
            showDgps={dgpsLoaded}
            editable={dgpsLoaded && !accepted}
            className="h-full"
            onPointsMoved={() => setPointsAdjusted(true)}
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {!dgpsLoaded ? (
            <button
              type="button"
              onClick={uploadData}
              className="inline-flex items-center gap-1.5 rounded-full bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-white"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload data
            </button>
          ) : null}

          {dgpsLoaded && !accepted ? (
            <button
              type="button"
              onClick={acceptGeoref}
              className="inline-flex items-center gap-1.5 rounded-full bg-emerald-600 px-4 py-2 text-xs font-medium text-white"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Accept
            </button>
          ) : null}
        </div>

        {accepted ? (
          <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
            Georeferencing accepted. DGPS control points committed to cadastral revision log.
          </div>
        ) : dgpsLoaded ? (
          <p className="mt-3 text-[11px] text-slate-500">Drag any DGPS point to adjust position, then click Accept.</p>
        ) : (
          <p className="mt-3 text-[11px] text-slate-500">Upload field data to populate DGPS control points on the map.</p>
        )}
      </section>
    </div>
  );
}

function GenericFlow({ workflowId }: { workflowId: WorkflowId }) {
  const cfg = WORKFLOW_LOOKUP[workflowId];
  const [step, setStep] = useState(0);
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");

  return (
    <div className="space-y-4">
      <WorkflowStepper steps={cfg.defaultSteps} activeStep={step} />
      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-[#1A1A1A]">{cfg.title} Interactive Demo</h3>
        <p className="mt-1 text-xs text-slate-500">{cfg.description}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Current stage</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">{cfg.defaultSteps[step]}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Decision</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">{status}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Demo payload</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">Puducherry synthetic data</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setStep((s) => Math.min(cfg.defaultSteps.length - 1, s + 1))}
            className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-4 py-2 text-xs text-white"
          >
            <Clock3 className="h-3.5 w-3.5" />
            Advance Stage
          </button>
          <button
            type="button"
            onClick={() => setStatus("approved")}
            className="inline-flex items-center gap-1 rounded-full bg-emerald-600 px-4 py-2 text-xs text-white"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Approve
          </button>
          <button
            type="button"
            onClick={() => setStatus("rejected")}
            className="inline-flex items-center gap-1 rounded-full bg-rose-600 px-4 py-2 text-xs text-white"
          >
            <CircleAlert className="h-3.5 w-3.5" />
            Reject
          </button>
        </div>
      </section>
    </div>
  );
}

export default function WorkflowDemoPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: WorkflowId }>();

  const workflow = useMemo(() => {
    if (!id) return null;
    return WORKFLOW_LOOKUP[id];
  }, [id]);

  if (!workflow) {
    return (
      <div className="min-h-screen bg-[#F7F7F5] p-4">
        <div className="mx-auto max-w-4xl rounded-2xl border border-slate-200 bg-white p-6">
          <p className="text-sm text-slate-600">Workflow could not be found.</p>
          <button onClick={() => navigate("/app")} className="mt-3 rounded-full bg-[#1A1A1A] px-4 py-2 text-xs text-white">
            Back to map
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-[#F7F7F5] p-4 pb-8 lg:p-5">
      <div className="mx-auto flex max-w-[1450px] flex-col gap-4">
        <section className="rounded-2xl border border-white/70 bg-white/85 p-4 shadow-[0_8px_30px_rgba(0,0,0,0.06)] backdrop-blur-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-lg font-semibold text-[#1A1A1A]">{workflow.title}</p>
              <p className="text-sm text-slate-500">{workflow.description}</p>
            </div>
            <button
              type="button"
              onClick={() => navigate("/app")}
              aria-label="Back"
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50 hover:text-slate-900"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          </div>

          {workflow.id === "online-mutation" ? <OnlineMutationFlow /> : null}
          {workflow.id === "georeferencing" ? <GeoreferencingFlow /> : null}
          {workflow.id === "anomaly-pipeline" ? <AnomalyPipelineFlow /> : null}
          {workflow.id !== "online-mutation" &&
          workflow.id !== "georeferencing" &&
          workflow.id !== "anomaly-pipeline" ? (
            <GenericFlow workflowId={workflow.id} />
          ) : null}
        </section>
      </div>
    </div>
  );
}
