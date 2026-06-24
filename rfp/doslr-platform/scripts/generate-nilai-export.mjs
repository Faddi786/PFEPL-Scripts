/**
 * One-time generator for NIL-AI report downloads.
 * Run: npm run generate:nilai-export
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { PDFDocument } from "pdf-lib";
import sharp from "sharp";
import { embedPdfFonts } from "./exportFonts.mjs";
import {
  RUN_TIMESTAMP,
  PDF_COLORS,
  drawPageChrome,
  drawSectionTitle,
  drawDataTable,
} from "./exportPdfLayout.mjs";
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
const outDir = join(root, "public", "exports", "nil-ai");
const mapRawPath = join(__dirname, "assets", "nilai-map-raw.png");
const mapRefinedPath = join(__dirname, "assets", "nilai-map-screenshot.png");

const META = {
  runId: "NIL-AI-2026-0611",
  region: "Puducherry",
  department: "Department of Survey & Land Records (DoSLR)",
  runDate: RUN_TIMESTAMP,
  generatedBy: "NIL-AI Cadastral Intelligence",
};

const PARCEL_ROWS = [
  ["42/1", "Kurumbapet", "Ward 2", "Residential", "647", "0.8%", "Green"],
  ["58/2", "Kurumbapet", "Ward 3", "Residential", "412", "2.4%", "Amber"],
  ["61", "Ariyankuppam", "Ward 5", "Agriculture", "892", "6.1%", "Red"],
  ["63/1", "Lawspet", "Ward 7", "Agriculture", "756", "3.2%", "Amber"],
  ["71/3", "Ariyankuppam", "Ward 6", "Agriculture", "534", "5.8%", "Red"],
  ["44/2", "Kurumbapet", "Ward 2", "Commercial", "318", "0.5%", "Green"],
];

const TABLE_HEADERS = ["Survey", "Village", "Ward", "Use", "Area", "Var%", "Band"];
const TABLE_COL_WEIGHTS = [0.1, 0.17, 0.12, 0.15, 0.11, 0.11, 0.12];

function columnWidthsFor(tableWidth) {
  const widths = TABLE_COL_WEIGHTS.map((weight) => Math.floor(tableWidth * weight));
  const used = widths.reduce((sum, value) => sum + value, 0);
  widths[widths.length - 1] += tableWidth - used;
  return widths;
}

async function prepareMapScreenshot() {
  try {
    const trimmed = await sharp(mapRawPath).trim({ threshold: 15 }).toBuffer();
    const { width, height } = await sharp(trimmed).metadata();
    const topCrop = 56;

    await sharp(trimmed)
      .extract({
        left: 0,
        top: topCrop,
        width,
        height: Math.max(1, height - topCrop),
      })
      .png()
      .toFile(mapRefinedPath);

    return readFile(mapRefinedPath);
  } catch {
    return readFile(mapRefinedPath);
  }
}

async function buildPdf(mapPngBuffer) {
  const pdf = await PDFDocument.create();
  const fonts = await embedPdfFonts(pdf);

  const page = pdf.addPage([842, 595]);
  const contentBox = drawPageChrome(page, fonts, {
    reportTitle: "NIL-AI Cadastral Analysis Report",
    reportSubtitle: `Run ${META.runId} · Generated ${RUN_TIMESTAMP}`,
    footerLeft: `${META.generatedBy} · ${META.region} · Confidential`,
    pageNumber: 1,
    pageTotal: 1,
    department: META.department,
  });

  const gap = 14;
  const mapX = contentBox.contentLeft;
  const mapW = Math.floor(contentBox.contentWidth * 0.5);
  const mapH = contentBox.contentTop - contentBox.contentBottom - 6;
  const mapY = contentBox.contentBottom + 4;

  const tableX = mapX + mapW + gap;
  const tableW = contentBox.contentRight - tableX;
  const colWidths = columnWidthsFor(tableW);

  const mapImage = await pdf.embedPng(mapPngBuffer);
  const scale = Math.min(mapW / mapImage.width, mapH / mapImage.height);
  const drawW = mapImage.width * scale;
  const drawH = mapImage.height * scale;
  const drawX = mapX + (mapW - drawW) / 2;
  const drawY = mapY + (mapH - drawH) / 2;

  page.drawImage(mapImage, {
    x: drawX,
    y: drawY,
    width: drawW,
    height: drawH,
  });

  page.drawRectangle({
    x: mapX,
    y: mapY,
    width: mapW,
    height: mapH,
    borderColor: PDF_COLORS.border,
    borderWidth: 0.8,
  });

  const tableTop = drawSectionTitle(page, fonts, tableX, contentBox.contentTop, "Attribute table");

  drawDataTable(page, fonts, {
    x: tableX,
    topY: tableTop,
    headers: TABLE_HEADERS,
    colWidths,
    rows: PARCEL_ROWS,
    rowHeight: 17,
  });

  return Buffer.from(await pdf.save());
}

async function buildExcel() {
  const workbook = createWorkbook();
  const sheet = workbook.addWorksheet("Attribute_Register");

  let row = addBrandTitle(sheet, "NIL-AI Parcel Attribute Register");
  row = addKeyValueBlock(sheet, row, [
    ["Run ID", META.runId],
    ["Region", META.region],
    ["Generated", RUN_TIMESTAMP],
  ]);
  row += 1;
  row = addSectionHeading(sheet, row, "Parcel attributes");
  addDataTable(
    sheet,
    row,
    ["Survey No", "Village", "Ward", "Land use", "Area (sq m)", "Variance %", "Band"],
    PARCEL_ROWS,
  );
  autofitSheet(sheet);

  return workbookToBuffer(workbook);
}

async function main() {
  const mapPngBuffer = await prepareMapScreenshot();
  const pdfBytes = await buildPdf(mapPngBuffer);
  const xlsxBytes = await buildExcel();

  await mkdir(outDir, { recursive: true });
  await writeFile(join(outDir, "NIL-AI-Cadastral-Analysis-Report.pdf"), pdfBytes);
  await writeFile(join(outDir, "NIL-AI-Parcel-Attribute-Register.xlsx"), xlsxBytes);

  console.log("NIL-AI exports written to public/exports/nil-ai/");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
