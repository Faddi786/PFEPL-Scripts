export type WorkflowId =
  | "online-mutation"
  | "georeferencing"
  | "certified-extract"
  | "anomaly-pipeline"
  | "search-rbac"
  | "citizen-search"
  | "mutation-sync-back"
  | "field-georeferencing";

export type WorkflowConfig = {
  id: WorkflowId;
  title: string;
  description: string;
  defaultSteps: string[];
};

export const WORKFLOW_CONFIGS: WorkflowConfig[] = [
  {
    id: "online-mutation",
    title: "Mutation",
    description: "Back-office officer splits parcel geometry, reviews before/after, and approves or rejects the mutation.",
    defaultSteps: ["Split parcel", "Review", "Approve/Reject", "Sync to all 3 databases real time"],
  },
  {
    id: "georeferencing",
    title: "Georeferencing",
    description: "Upload DGPS field data, adjust control points on the map, and accept the georeferencing solution.",
    defaultSteps: ["Upload data", "Adjust DGPS points", "Accept"],
  },
  {
    id: "certified-extract",
    title: "Certified Extract",
    description: "Generate certified parcel extract with audit lock and issue stamp.",
    defaultSteps: ["Search parcel", "Generate draft", "Officer attestation", "Seal document", "Issue copy"],
  },
  {
    id: "anomaly-pipeline",
    title: "Anomaly Pipeline",
    description: "Variance bands and record-map checks feed the minister dashboard.",
    defaultSteps: ["Scheduled run", "Area compare", "Variance bands", "Record-map checks", "Persist & dashboard"],
  },
  {
    id: "search-rbac",
    title: "Search + RBAC",
    description: "Role-based search controls with selective owner field exposure.",
    defaultSteps: ["Role login", "Search request", "Policy enforcement", "Result mask", "Audit event"],
  },
  {
    id: "citizen-search",
    title: "Citizen Search",
    description: "Public/citizen search journey for parcel reference and extracts.",
    defaultSteps: ["Enter survey/ULPIN", "Validate scope", "Render parcel", "Request extract", "Track status"],
  },
  {
    id: "mutation-sync-back",
    title: "Mutation Sync-Back",
    description: "Sync approved mutation to backend ledger and dependent systems.",
    defaultSteps: ["Mutation approved", "Queue sync", "Push transaction", "Acknowledgement", "State updated"],
  },
  {
    id: "field-georeferencing",
    title: "Field Georeferencing",
    description: "DGPS field checks and georeferencing reconciliation loop.",
    defaultSteps: ["Load baseline", "Capture DGPS", "Compute offset", "Review residual", "Publish update"],
  },
];

export const WORKFLOW_LOOKUP = Object.fromEntries(WORKFLOW_CONFIGS.map((cfg) => [cfg.id, cfg]));
