import * as XLSX from "xlsx";

/** Set column widths from cell content (SheetJS autofit approximation). */
export function autofitColumns(worksheet) {
  if (!worksheet["!ref"]) return;

  const range = XLSX.utils.decode_range(worksheet["!ref"]);
  const widths = [];

  for (let col = range.s.c; col <= range.e.c; col += 1) {
    let maxLen = 8;
    for (let row = range.s.r; row <= range.e.r; row += 1) {
      const cell = worksheet[XLSX.utils.encode_cell({ r: row, c: col })];
      if (!cell || cell.v == null) continue;
      const text = String(cell.v);
      maxLen = Math.max(maxLen, text.length);
    }
    widths.push({ wch: Math.min(maxLen + 2, 72) });
  }

  worksheet["!cols"] = widths;
}

export function sheetFromAoA(data) {
  const worksheet = XLSX.utils.aoa_to_sheet(data);
  autofitColumns(worksheet);
  return worksheet;
}

export function appendSheet(wb, data, name) {
  XLSX.utils.book_append_sheet(wb, sheetFromAoA(data), name);
}
