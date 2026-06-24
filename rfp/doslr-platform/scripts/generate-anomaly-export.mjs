/**
 * One-time generator for the anomaly export bundle.
 * Run: npm run generate:anomaly-export
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import JSZip from "jszip";
import { PDFDocument } from "pdf-lib";
import { embedPdfFonts, SVG_FONT_STACK } from "./exportFonts.mjs";
import {
  BRAND_NAME,
  RUN_TIMESTAMP,
  PDF_COLORS,
  drawPageChrome,
  drawKeyValueLine,
  drawSectionTitle,
  drawDataTable,
} from "./exportPdfLayout.mjs";
import { PDF_TYPO } from "./exportFonts.mjs";
import {
  createWorkbook,
  addBrandTitle,
  addKeyValueBlock,
  addSectionHeading,
  addDataTable,
  autofitSheet,
  workbookToBuffer,
} from "./exportExcel.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const outDir = join(root, "public", "exports");
const zipPath = join(outDir, "DOSLR-Anomaly-Export-2026.zip");
const mapScreenshotPath = join(__dirname, "assets", "anomaly-analysis-map.png");

const RUN_META = {
  runId: "DOSLR-ANOM-2026-0611",
  region: "Puducherry",
  taluk: "Puducherry",
  village: "Muthialpet",
  ward: "Ward 2–4 cluster",
  scopeParcels: 50,
  runDate: RUN_TIMESTAMP,
  department: "Department of Survey & Land Records (DoSLR)",
};

const VILLAGES = ["Muthialpet", "Kurumbapet", "Ariyankuppam", "Lawspet"];
const LAND_USES = ["Residential", "Agriculture", "Commercial"];

function bandForIndex(index) {
  if (index % 7 === 0 || index % 11 === 0) return "red";
  if (index % 3 === 0 || index % 5 === 0) return "amber";
  return "green";
}

function variancePct(band, index) {
  const seed = (index * 17 + 3) % 100;
  if (band === "green") return Number((0.4 + (seed % 55) / 100).toFixed(2));
  if (band === "amber") return Number((1.2 + (seed % 35) / 10).toFixed(2));
  return Number((5.5 + (seed % 42) / 10).toFixed(2));
}

function buildParcelRows() {
  return Array.from({ length: 50 }, (_, index) => {
    const band = bandForIndex(index);
    const village = VILLAGES[index % VILLAGES.length];
    const surveyNo = `${40 + Math.floor(index / 3)}/${(index % 4) + 1}`;
    const areaSqM = 420 + (index % 9) * 38 + (index % 3) * 12;
    const stAreaSqM = Number((areaSqM * (1 + variancePct(band, index) / 100)).toFixed(1));
    const flags = [];
    if ([2, 7, 18, 31].includes(index)) flags.push("Missing geometry");
    if ([5, 22, 41].includes(index)) flags.push("ULPIN conflict");
    if ([1, 4, 9, 14, 23, 28, 36, 44].includes(index)) flags.push("Classification mismatch");
    if (band !== "green") flags.push("Boundary deviation");

    return {
      sNo: index + 1,
      surveyNo,
      ulpin: `36${String(index).padStart(2, "0")}PU2026${String(1000 + index)}`,
      village,
      ward: `Ward ${(index % 4) + 2}`,
      landUse: LAND_USES[index % 3],
      areaRorSqM: areaSqM,
      stAreaSqM,
      variancePct: variancePct(band, index),
      varianceBand: band.toUpperCase(),
      boundaryFlag: band !== "green" ? "YES" : "NO",
      recordMapFlags: flags.length ? flags.join("; ") : "—",
      recommendedAction:
        band === "red"
          ? "Field verification + RoR correction"
          : band === "amber"
            ? "Desk review + digitized boundary reconcile"
            : "No action",
    };
  });
}

function bandCounts(rows) {
  return rows.reduce(
    (acc, row) => {
      acc[row.varianceBand.toLowerCase()] += 1;
      return acc;
    },
    { green: 0, amber: 0, red: 0 },
  );
}

const BAND_THEME = {
  green: { fill: "#6d9b82", stroke: "#3f5f4d", fillOpacity: 0.82, label: "Within tolerance (at most 1%)" },
  amber: { fill: "#c9a06a", stroke: "#8a6b3f", fillOpacity: 0.84, label: "Moderate variance (1-5%)" },
  red: { fill: "#b86b6b", stroke: "#7a4343", fillOpacity: 0.86, label: "High variance (above 5%)" },
};

function escapeXml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadMapScreenshot() {
  return readFile(mapScreenshotPath);
}

function buildHeatMapSvg(rows, counts, mapScreenshotB64) {
  const width = 1400;
  const height = 900;
  const mapX = 32;
  const mapY = 88;
  const mapW = 860;
  const mapH = 780;
  const panelX = mapX + mapW + 28;
  const panelW = width - panelX - 32;

  const avgVariance = (rows.reduce((sum, row) => sum + row.variancePct, 0) / rows.length).toFixed(2);
  const flaggedCount = rows.filter((row) => row.recordMapFlags !== "—").length;
  const maxVariance = Math.max(...rows.map((row) => row.variancePct)).toFixed(2);

  const total = rows.length;
  const barMaxW = panelW - 48;
  function barRow(label, count, color, y) {
    const pct = count / total;
    const barW = Math.max(8, barMaxW * pct);
    return `
      <text x="${panelX + 20}" y="${y}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">${escapeXml(label)}</text>
      <text x="${panelX + panelW - 20}" y="${y}" text-anchor="end" font-family=${SVG_FONT_STACK} font-size="10" font-weight="600" fill="#111111">${count} (${Math.round(pct * 100)}%)</text>
      <rect x="${panelX + 20}" y="${y + 8}" width="${barMaxW}" height="10" rx="5" fill="#e8edf2"/>
      <rect x="${panelX + 20}" y="${y + 8}" width="${barW}" height="10" rx="5" fill="${color}"/>
    `;
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <clipPath id="mapClip">
      <rect x="${mapX}" y="${mapY}" width="${mapW}" height="${mapH}" rx="12"/>
    </clipPath>
    <filter id="mapShadow" x="-2%" y="-2%" width="104%" height="104%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.16"/>
    </filter>
  </defs>

  <rect width="100%" height="100%" fill="#f7f7f7"/>

  <rect x="0" y="0" width="${width}" height="64" fill="#000000"/>
  <text x="32" y="28" font-family=${SVG_FONT_STACK} font-size="18" font-weight="700" fill="#ffffff">${BRAND_NAME}</text>
  <text x="32" y="48" font-family=${SVG_FONT_STACK} font-size="11" fill="#d4d4d4">DoSLR Variance Heat Map · ${escapeXml(RUN_META.village)} cluster · ${RUN_META.scopeParcels} parcels</text>
  <text x="${width - 32}" y="36" text-anchor="end" font-family=${SVG_FONT_STACK} font-size="9" fill="#e5e5e5">Run ${escapeXml(RUN_META.runId)} · ${escapeXml(RUN_TIMESTAMP)}</text>

  <image href="data:image/png;base64,${mapScreenshotB64}" x="${mapX}" y="${mapY}" width="${mapW}" height="${mapH}" preserveAspectRatio="xMidYMid slice" clip-path="url(#mapClip)" filter="url(#mapShadow)"/>
  <rect x="${mapX}" y="${mapY}" width="${mapW}" height="${mapH}" rx="12" fill="none" stroke="#d4d4d4" stroke-width="1"/>

  <rect x="${panelX}" y="${mapY}" width="${panelW}" height="${mapH}" rx="12" fill="#ffffff" stroke="#d4d4d4" stroke-width="1"/>
  <text x="${panelX + 20}" y="${mapY + 28}" font-family=${SVG_FONT_STACK} font-size="14" font-weight="700" fill="#000000">Data analysis</text>
  <line x1="${panelX + 20}" y1="${mapY + 36}" x2="${panelX + panelW - 20}" y2="${mapY + 36}" stroke="#e2e8f0" stroke-width="1"/>

  <text x="${panelX + 20}" y="${mapY + 62}" font-family=${SVG_FONT_STACK} font-size="11" font-weight="600" fill="#000000">Scope summary</text>
  <text x="${panelX + 20}" y="${mapY + 82}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">Region: ${RUN_META.region} · Taluk: ${RUN_META.taluk}</text>
  <text x="${panelX + 20}" y="${mapY + 100}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">Village cluster: ${RUN_META.village} (${RUN_META.ward})</text>
  <text x="${panelX + 20}" y="${mapY + 118}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">Parcels analysed: ${total}</text>
  <text x="${panelX + 20}" y="${mapY + 136}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">Mean variance: ${avgVariance}% · Max: ${maxVariance}%</text>
  <text x="${panelX + 20}" y="${mapY + 154}" font-family=${SVG_FONT_STACK} font-size="10" fill="#475569">Record-map flags: ${flaggedCount} parcels</text>

  <text x="${panelX + 20}" y="${mapY + 186}" font-family=${SVG_FONT_STACK} font-size="11" font-weight="600" fill="#000000">Variance band distribution</text>
  ${barRow("Within tolerance", counts.green, BAND_THEME.green.fill, mapY + 200)}
  ${barRow("Moderate variance", counts.amber, BAND_THEME.amber.fill, mapY + 232)}
  ${barRow("High variance", counts.red, BAND_THEME.red.fill, mapY + 264)}

  <text x="${panelX + 20}" y="${mapY + 310}" font-family=${SVG_FONT_STACK} font-size="11" font-weight="600" fill="#000000">Record-map checks</text>
  <text x="${panelX + 20}" y="${mapY + 330}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">Missing RoR — PASS</text>
  <text x="${panelX + 20}" y="${mapY + 348}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">Missing geometry — 4 flagged</text>
  <text x="${panelX + 20}" y="${mapY + 366}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">ULPIN conflict — 3 flagged</text>
  <text x="${panelX + 20}" y="${mapY + 384}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">Classification mismatch — 8 flagged</text>

  <text x="${panelX + 20}" y="${mapY + 418}" font-family=${SVG_FONT_STACK} font-size="11" font-weight="600" fill="#000000">Key findings</text>
  <text x="${panelX + 20}" y="${mapY + 438}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">- ${counts.red} parcels exceed 5% ST_Area vs RoR deviation</text>
  <text x="${panelX + 20}" y="${mapY + 456}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">- ${counts.amber} parcels require desk reconciliation</text>
  <text x="${panelX + 20}" y="${mapY + 474}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">- Boundary deviation flags on amber/red cohort</text>
  <text x="${panelX + 20}" y="${mapY + 492}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">- Field verification recommended for red-band parcels</text>

  <text x="${panelX + 20}" y="${mapY + 526}" font-family=${SVG_FONT_STACK} font-size="11" font-weight="600" fill="#000000">Legend</text>
  <polygon points="${panelX + 20},${mapY + 544} ${panelX + 38},${mapY + 544} ${panelX + 32},${mapY + 558}" fill="${BAND_THEME.green.fill}" stroke="${BAND_THEME.green.stroke}" stroke-width="1"/>
  <text x="${panelX + 46}" y="${mapY + 554}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">${escapeXml(BAND_THEME.green.label)}</text>
  <polygon points="${panelX + 20},${mapY + 568} ${panelX + 38},${mapY + 568} ${panelX + 32},${mapY + 582}" fill="${BAND_THEME.amber.fill}" stroke="${BAND_THEME.amber.stroke}" stroke-width="1"/>
  <text x="${panelX + 46}" y="${mapY + 578}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">${escapeXml(BAND_THEME.amber.label)}</text>
  <polygon points="${panelX + 20},${mapY + 592} ${panelX + 38},${mapY + 592} ${panelX + 32},${mapY + 606}" fill="${BAND_THEME.red.fill}" stroke="${BAND_THEME.red.stroke}" stroke-width="1"/>
  <text x="${panelX + 46}" y="${mapY + 602}" font-family=${SVG_FONT_STACK} font-size="9" fill="#475569">${escapeXml(BAND_THEME.red.label)}</text>

  <rect x="0" y="${height - 36}" width="${width}" height="36" fill="#e8edf2"/>
  <text x="32" y="${height - 14}" font-family=${SVG_FONT_STACK} font-size="8" fill="#64748b">${RUN_META.department} · Confidential</text>
  <text x="${width - 32}" y="${height - 14}" text-anchor="end" font-family=${SVG_FONT_STACK} font-size="8" fill="#64748b">Generated by DoSLR Anomaly Pipeline</text>
</svg>`;
}

async function buildPdf(rows, mapPngBuffer) {
  const pdf = await PDFDocument.create();
  const fonts = await embedPdfFonts(pdf);

  const cover = pdf.addPage([595, 842]);
  const coverBox = drawPageChrome(cover, fonts, {
    reportTitle: "Cadastral Anomaly Pipeline Report",
    reportSubtitle: `Run ${RUN_META.runId} · Generated ${RUN_TIMESTAMP}`,
    footerLeft: `${RUN_META.department} · Confidential`,
    pageNumber: 1,
    pageTotal: 2,
    department: RUN_META.department,
  });

  let coverY = coverBox.contentTop;
  [
    ["Run ID", RUN_META.runId],
    ["Region / Taluk", `${RUN_META.region} / ${RUN_META.taluk}`],
    ["Analysis cluster", `${RUN_META.village} (${RUN_META.ward})`],
    ["Run date", RUN_TIMESTAMP],
    ["Scoped parcels", RUN_META.scopeParcels],
  ].forEach(([key, value]) => {
    drawKeyValueLine(cover, fonts, coverBox.contentLeft, coverY, key, value);
    coverY -= 20;
  });

  const analysis = pdf.addPage([595, 842]);
  const analysisBox = drawPageChrome(analysis, fonts, {
    reportTitle: "Variance Analysis",
    reportSubtitle: "Satellite basemap with variance band overlay (analysis complete)",
    footerLeft: `${RUN_META.department} · Confidential`,
    pageNumber: 2,
    pageTotal: 2,
    department: RUN_META.department,
  });

  const mapImage = await pdf.embedPng(mapPngBuffer);
  const mapWidth = analysisBox.contentWidth;
  const mapHeight = (mapImage.height / mapImage.width) * mapWidth;
  const mapTop = analysisBox.contentTop;
  const mapY = mapTop - mapHeight;

  analysis.drawImage(mapImage, {
    x: analysisBox.contentLeft,
    y: mapY,
    width: mapWidth,
    height: mapHeight,
  });
  analysis.drawRectangle({
    x: analysisBox.contentLeft,
    y: mapY,
    width: mapWidth,
    height: mapHeight,
    borderColor: PDF_COLORS.border,
    borderWidth: 0.9,
  });

  let tableTop = drawSectionTitle(
    analysis,
    fonts,
    analysisBox.contentLeft,
    mapY - 22,
    "Top variance parcels (red band)",
  );

  const redRows = rows
    .filter((row) => row.varianceBand === "RED")
    .slice(0, 10)
    .map((row) => [
      row.surveyNo,
      row.village,
      row.areaRorSqM,
      row.stAreaSqM,
      row.variancePct,
      row.recommendedAction,
    ]);

  const tableBottom = drawDataTable(analysis, fonts, {
    x: analysisBox.contentLeft,
    topY: tableTop,
    headers: ["Survey", "Village", "RoR sq m", "ST sq m", "Var %", "Action"],
    colWidths: [54, 82, 54, 54, 40, 180],
    rows: redRows,
  });

  let actionY = drawSectionTitle(
    analysis,
    fonts,
    analysisBox.contentLeft,
    tableBottom - 6,
    "Recommended actions",
  );

  [
    "- Approve field verification squad for red-band parcels within 15 days",
    "- Direct RoR desk reconciliation for amber-band parcels",
    "- Resolve ULPIN conflicts before next mutation sync window",
  ].forEach((line) => {
    analysis.drawText(line, {
      x: analysisBox.contentLeft,
      y: actionY,
      size: PDF_TYPO.body,
      font: fonts.regular,
      color: PDF_COLORS.ink,
    });
    actionY -= 14;
  });

  return Buffer.from(await pdf.save());
}

async function buildExcel(rows, counts) {
  const workbook = createWorkbook();

  const summary = workbook.addWorksheet("Summary");
  let row = addBrandTitle(summary, "DoSLR Anomaly Pipeline — Summary");
  row = addKeyValueBlock(summary, row, [
    ["Run ID", RUN_META.runId],
    ["Region", RUN_META.region],
    ["Village cluster", RUN_META.village],
    ["Run date", RUN_TIMESTAMP],
    ["Scoped parcels", RUN_META.scopeParcels],
  ]);
  row += 1;
  row = addSectionHeading(summary, row, "Variance band distribution");
  row = addDataTable(
    summary,
    row,
    ["Variance band", "Count", "Threshold"],
    [
      ["Green", counts.green, "at most 1%"],
      ["Amber", counts.amber, "1-5%"],
      ["Red", counts.red, "> 5%"],
    ],
  );
  row += 1;
  row = addSectionHeading(summary, row, "Record-map checks");
  addDataTable(
    summary,
    row,
    ["Check", "Status", "Detail"],
    [
      ["Missing RoR", "PASS", "All scoped parcels have linked RoR records"],
      ["Missing geometry", "FLAGGED", "4 parcels — geometry null in cadastral store"],
      ["Duplicate geom", "PASS", "No overlapping parcel footprints detected"],
      ["ULPIN conflict", "FLAGGED", "3 duplicate ULPIN candidates in Ward 2 batch"],
      ["Classification mismatch", "FLAGGED", "8 parcels — land-use vs ownership class mismatch"],
    ],
  );
  autofitSheet(summary);

  const register = workbook.addWorksheet("Anomaly_Register");
  row = addBrandTitle(register, "Anomaly parcel register");
  row = addKeyValueBlock(register, row, [
    ["Run ID", RUN_META.runId],
    ["Run date", RUN_TIMESTAMP],
  ]);
  row += 1;
  addDataTable(
    register,
    row,
    [
      "S.No",
      "Survey No",
      "ULPIN",
      "Village",
      "Ward",
      "Land use",
      "RoR area (sq m)",
      "ST_Area (sq m)",
      "Variance %",
      "Band",
      "Boundary flag",
      "Record-map flags",
      "Recommended action",
    ],
    rows.map((item) => [
      item.sNo,
      item.surveyNo,
      item.ulpin,
      item.village,
      item.ward,
      item.landUse,
      item.areaRorSqM,
      item.stAreaSqM,
      item.variancePct,
      item.varianceBand,
      item.boundaryFlag,
      item.recordMapFlags,
      item.recommendedAction,
    ]),
  );
  autofitSheet(register);

  return workbookToBuffer(workbook);
}

async function main() {
  const rows = buildParcelRows();
  const counts = bandCounts(rows);
  const mapScreenshot = await loadMapScreenshot();
  const mapScreenshotB64 = mapScreenshot.toString("base64");
  const pdfBytes = await buildPdf(rows, mapScreenshot);
  const xlsxBytes = await buildExcel(rows, counts);
  const svg = buildHeatMapSvg(rows, counts, mapScreenshotB64);

  const zip = new JSZip();
  zip.file("DOSLR_Variance_Analysis_Report.pdf", pdfBytes);
  zip.file("Anomaly_Parcel_Register.xlsx", xlsxBytes);
  zip.file("Variance_Heat_Map.svg", svg);

  const zipBuffer = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } });

  await mkdir(outDir, { recursive: true });
  await writeFile(zipPath, zipBuffer);

  console.log(`Created ${zipPath} (${(zipBuffer.length / 1024).toFixed(1)} KB)`);
  console.log(`Parcels: ${rows.length} | Green: ${counts.green} Amber: ${counts.amber} Red: ${counts.red}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
