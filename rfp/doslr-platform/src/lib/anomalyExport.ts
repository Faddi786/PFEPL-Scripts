/** Pre-generated export bundle — created once via `npm run generate:anomaly-export`. */
export const ANOMALY_EXPORT_FILENAME = "DOSLR-Anomaly-Export-2026.zip";
export const ANOMALY_EXPORT_URL = `/exports/${ANOMALY_EXPORT_FILENAME}`;

export function downloadAnomalyExportBundle() {
  const anchor = document.createElement("a");
  anchor.href = ANOMALY_EXPORT_URL;
  anchor.download = ANOMALY_EXPORT_FILENAME;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
}
