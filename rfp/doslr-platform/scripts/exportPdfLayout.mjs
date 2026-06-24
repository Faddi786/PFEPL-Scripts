import { rgb } from "pdf-lib";
import { PDF_TYPO } from "./exportFonts.mjs";

export const BRAND_NAME = "NILAM";
export const RUN_TIMESTAMP = "11 June 2026, 2:03 pm";

export const PDF_COLORS = {
  ink: rgb(0.1, 0.12, 0.16),
  muted: rgb(0.45, 0.48, 0.52),
  border: rgb(0.72, 0.75, 0.78),
  borderLight: rgb(0.84, 0.87, 0.9),
  headerBg: rgb(0, 0, 0),
  headerSub: rgb(0.82, 0.82, 0.82),
  accent: rgb(0, 0, 0),
  tableHead: rgb(0.93, 0.94, 0.96),
  white: rgb(1, 1, 1),
};

const MARGIN = 40;

export function drawPageChrome(page, fonts, options) {
  const { width, height } = page.getSize();
  const {
    reportTitle,
    reportSubtitle,
    footerLeft,
    pageNumber,
    pageTotal,
    department,
  } = options;

  const semibold = fonts.semibold ?? fonts.bold;

  page.drawRectangle({
    x: MARGIN,
    y: MARGIN,
    width: width - MARGIN * 2,
    height: height - MARGIN * 2,
    borderColor: PDF_COLORS.border,
    borderWidth: 0.9,
    color: PDF_COLORS.white,
  });

  page.drawRectangle({
    x: MARGIN + 2.5,
    y: MARGIN + 2.5,
    width: width - MARGIN * 2 - 5,
    height: height - MARGIN * 2 - 5,
    borderColor: PDF_COLORS.borderLight,
    borderWidth: 0.45,
  });

  page.drawRectangle({
    x: MARGIN,
    y: height - MARGIN - 3,
    width: width - MARGIN * 2,
    height: 3,
    color: PDF_COLORS.accent,
  });

  page.drawRectangle({
    x: MARGIN + 1,
    y: height - MARGIN - 56,
    width: width - MARGIN * 2 - 2,
    height: 52,
    color: PDF_COLORS.headerBg,
  });

  page.drawText(BRAND_NAME, {
    x: MARGIN + 16,
    y: height - MARGIN - 30,
    size: PDF_TYPO.brand,
    font: fonts.bold,
    color: PDF_COLORS.white,
  });

  const dept = department ?? "Department of Survey & Land Records (DoSLR)";
  page.drawText(dept, {
    x: MARGIN + 16,
    y: height - MARGIN - 46,
    size: PDF_TYPO.brandSub,
    font: fonts.regular,
    color: PDF_COLORS.headerSub,
  });

  if (pageNumber && pageTotal) {
    const label = `Page ${pageNumber} of ${pageTotal}`;
    const labelW = fonts.regular.widthOfTextAtSize(label, PDF_TYPO.pageLabel);
    page.drawText(label, {
      x: width - MARGIN - 16 - labelW,
      y: height - MARGIN - 36,
      size: PDF_TYPO.pageLabel,
      font: fonts.regular,
      color: PDF_COLORS.headerSub,
    });
  }

  page.drawText(reportTitle, {
    x: MARGIN + 16,
    y: height - MARGIN - 78,
    size: PDF_TYPO.reportTitle,
    font: fonts.bold,
    color: PDF_COLORS.ink,
  });

  if (reportSubtitle) {
    page.drawText(reportSubtitle, {
      x: MARGIN + 16,
      y: height - MARGIN - 94,
      size: PDF_TYPO.reportSubtitle,
      font: fonts.regular,
      color: PDF_COLORS.muted,
    });
  }

  page.drawLine({
    start: { x: MARGIN + 16, y: MARGIN + 30 },
    end: { x: width - MARGIN - 16, y: MARGIN + 30 },
    thickness: 0.5,
    color: PDF_COLORS.border,
  });

  const footer = footerLeft ?? `${dept} · Confidential`;
  page.drawText(footer, {
    x: MARGIN + 16,
    y: MARGIN + 16,
    size: PDF_TYPO.footer,
    font: fonts.regular,
    color: PDF_COLORS.muted,
  });

  return {
    contentTop: height - MARGIN - 110,
    contentLeft: MARGIN + 16,
    contentRight: width - MARGIN - 16,
    contentBottom: MARGIN + 44,
    contentWidth: width - MARGIN * 2 - 32,
  };
}

export function drawKeyValueLine(page, fonts, x, y, key, value) {
  page.drawText(`${key}:`, {
    x,
    y,
    size: PDF_TYPO.keyValue,
    font: fonts.bold,
    color: PDF_COLORS.ink,
  });
  const keyWidth = fonts.bold.widthOfTextAtSize(`${key}:`, PDF_TYPO.keyValue);
  page.drawText(String(value), {
    x: x + keyWidth + 10,
    y,
    size: PDF_TYPO.keyValue,
    font: fonts.regular,
    color: PDF_COLORS.ink,
  });
}

export function drawSectionTitle(page, fonts, x, y, title) {
  const semibold = fonts.semibold ?? fonts.bold;
  page.drawText(title, {
    x,
    y,
    size: PDF_TYPO.section,
    font: semibold,
    color: PDF_COLORS.ink,
  });
  return y - 20;
}

export function drawDataTable(page, fonts, { x, topY, headers, rows, colWidths, rowHeight = 18 }) {
  const semibold = fonts.semibold ?? fonts.bold;
  let y = topY;
  let cx = x;

  headers.forEach((header, index) => {
    page.drawRectangle({
      x: cx,
      y: y - rowHeight,
      width: colWidths[index],
      height: rowHeight,
      borderColor: PDF_COLORS.border,
      borderWidth: 0.6,
      color: PDF_COLORS.tableHead,
    });
    page.drawText(header, {
      x: cx + 6,
      y: y - rowHeight + 6,
      size: PDF_TYPO.tableHeader,
      font: semibold,
      color: PDF_COLORS.ink,
    });
    cx += colWidths[index];
  });

  y -= rowHeight;

  rows.forEach((row) => {
    y -= rowHeight;
    cx = x;
    row.forEach((cell, index) => {
      page.drawRectangle({
        x: cx,
        y,
        width: colWidths[index],
        height: rowHeight,
        borderColor: PDF_COLORS.border,
        borderWidth: 0.5,
      });
      const text = String(cell).length > 42 ? `${String(cell).slice(0, 39)}...` : String(cell);
      page.drawText(text, {
        x: cx + 6,
        y: y + 6,
        size: PDF_TYPO.tableBody,
        font: fonts.regular,
        color: PDF_COLORS.ink,
      });
      cx += colWidths[index];
    });
  });

  return y - 10;
}
