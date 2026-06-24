import ExcelJS from "exceljs";
import { EXCEL_FONT, EXCEL_TYPO } from "./exportFonts.mjs";

const BORDER = {
  top: { style: "thin", color: { argb: "FFB0B8C4" } },
  left: { style: "thin", color: { argb: "FFB0B8C4" } },
  bottom: { style: "thin", color: { argb: "FFB0B8C4" } },
  right: { style: "thin", color: { argb: "FFB0B8C4" } },
};

const HEADER_FILL = {
  type: "pattern",
  pattern: "solid",
  fgColor: { argb: "FFEEF2F7" },
};

const BRAND_FILL = {
  type: "pattern",
  pattern: "solid",
  fgColor: { argb: "FF000000" },
};

function leftAlign(cell) {
  cell.alignment = { horizontal: "left", vertical: "middle", wrapText: true };
}

function applyBorder(cell) {
  cell.border = BORDER;
}

function styleHeader(cell) {
  leftAlign(cell);
  applyBorder(cell);
  cell.font = { name: EXCEL_FONT, size: EXCEL_TYPO.header, bold: true, color: { argb: "FF1A1F29" } };
  cell.fill = HEADER_FILL;
}

function styleKey(cell) {
  leftAlign(cell);
  applyBorder(cell);
  cell.font = { name: EXCEL_FONT, size: EXCEL_TYPO.key, bold: true, color: { argb: "FF1A1F29" } };
}

function styleValue(cell) {
  leftAlign(cell);
  applyBorder(cell);
  cell.font = { name: EXCEL_FONT, size: EXCEL_TYPO.body, color: { argb: "FF334155" } };
}

function styleBody(cell) {
  leftAlign(cell);
  applyBorder(cell);
  cell.font = { name: EXCEL_FONT, size: EXCEL_TYPO.body, color: { argb: "FF334155" } };
}

export function createWorkbook() {
  return new ExcelJS.Workbook();
}

export function addBrandTitle(sheet, title) {
  sheet.mergeCells(1, 1, 1, 6);
  const brand = sheet.getCell(1, 1);
  brand.value = "NILAM";
  brand.font = { name: EXCEL_FONT, size: EXCEL_TYPO.brand, bold: true, color: { argb: "FFFFFFFF" } };
  brand.fill = BRAND_FILL;
  brand.alignment = { horizontal: "left", vertical: "middle" };
  brand.border = BORDER;

  sheet.mergeCells(2, 1, 2, 6);
  const subtitle = sheet.getCell(2, 1);
  subtitle.value = title;
  subtitle.font = { name: EXCEL_FONT, size: EXCEL_TYPO.subtitle, bold: true, color: { argb: "FF1A1F29" } };
  subtitle.alignment = { horizontal: "left", vertical: "middle" };
  subtitle.border = BORDER;

  sheet.getRow(1).height = 26;
  sheet.getRow(2).height = 22;
  return 4;
}

export function addKeyValueBlock(sheet, startRow, pairs) {
  let row = startRow;
  pairs.forEach(([key, value]) => {
    const keyCell = sheet.getCell(row, 1);
    keyCell.value = key;
    styleKey(keyCell);

    sheet.mergeCells(row, 2, row, 6);
    const valueCell = sheet.getCell(row, 2);
    valueCell.value = value;
    styleValue(valueCell);
    row += 1;
  });
  return row;
}

export function addSectionHeading(sheet, row, text, colSpan = 6) {
  sheet.mergeCells(row, 1, row, colSpan);
  const cell = sheet.getCell(row, 1);
  cell.value = text;
  cell.font = { name: EXCEL_FONT, size: EXCEL_TYPO.section, bold: true, color: { argb: "FF1A1F29" } };
  cell.alignment = { horizontal: "left", vertical: "middle" };
  cell.border = BORDER;
  cell.fill = HEADER_FILL;
  sheet.getRow(row).height = 20;
  return row + 1;
}

export function addDataTable(sheet, startRow, headers, rows) {
  headers.forEach((header, index) => {
    const cell = sheet.getCell(startRow, index + 1);
    cell.value = header;
    styleHeader(cell);
  });
  sheet.getRow(startRow).height = 20;

  rows.forEach((rowValues, rowIndex) => {
    const excelRow = sheet.getRow(startRow + 1 + rowIndex);
    excelRow.height = 18;
    rowValues.forEach((value, colIndex) => {
      const cell = sheet.getCell(startRow + 1 + rowIndex, colIndex + 1);
      cell.value = value;
      styleBody(cell);
    });
  });

  return startRow + 1 + rows.length;
}

export function autofitSheet(sheet) {
  const colWidths = [];
  sheet.eachRow({ includeEmpty: false }, (row) => {
    row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
      const length = String(cell.value ?? "").length + 2;
      colWidths[colNumber] = Math.max(colWidths[colNumber] ?? 10, Math.min(length, 56));
    });
  });

  colWidths.forEach((width, index) => {
    if (index > 0) sheet.getColumn(index).width = width;
  });
}

export async function workbookToBuffer(workbook) {
  const buffer = await workbook.xlsx.writeBuffer();
  return Buffer.from(buffer);
}
