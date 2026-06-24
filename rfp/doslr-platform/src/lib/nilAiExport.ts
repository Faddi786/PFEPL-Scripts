/** Pre-generated NIL-AI report files — created once via `npm run generate:nilai-export`. */
export type NilAiAttachment = {
  id: string;
  title: string;
  subtitle: string;
  url: string;
  filename: string;
  kind: "pdf" | "xlsx";
};

export const NIL_AI_EXPORTS = {
  pdf: {
    filename: "NIL-AI-Cadastral-Analysis-Report.pdf",
    url: "/exports/nil-ai/NIL-AI-Cadastral-Analysis-Report.pdf",
    title: "Cadastral analysis report",
    subtitle: "Document · PDF",
  },
  xlsx: {
    filename: "NIL-AI-Parcel-Attribute-Register.xlsx",
    url: "/exports/nil-ai/NIL-AI-Parcel-Attribute-Register.xlsx",
    title: "Parcel attribute register",
    subtitle: "Spreadsheet · XLSX",
  },
} as const;

export function openNilAiFile(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}
