import fontkit from "@pdf-lib/fontkit";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { StandardFonts } from "pdf-lib";

const __dirname = dirname(fileURLToPath(import.meta.url));
const fontsDir = join(__dirname, "fonts");

export const FONT_FAMILY = "Source Sans 3";
export const EXCEL_FONT = "Calibri";
export const SVG_FONT_STACK = "Source Sans 3, Helvetica Neue, Arial, sans-serif";

/** PDF type hierarchy (pt) — institutional report scale */
export const PDF_TYPO = {
  brand: 18,
  brandSub: 8,
  reportTitle: 15,
  reportSubtitle: 9,
  section: 11,
  body: 10,
  tableHeader: 9,
  tableBody: 9,
  caption: 8,
  footer: 7.5,
  keyValue: 10,
  pageLabel: 7.5,
};

/** Excel type hierarchy (pt) — aligned with PDF where possible */
export const EXCEL_TYPO = {
  brand: 17,
  subtitle: 12,
  section: 11,
  header: 11,
  body: 10,
  key: 10,
};

/**
 * Embed Source Sans 3 (Regular, Bold, Semibold) into a PDFDocument.
 * Falls back to Helvetica if font files are unavailable.
 */
export async function embedPdfFonts(pdfDoc) {
  pdfDoc.registerFontkit(fontkit);

  try {
    const [regularBytes, boldBytes, semiboldBytes] = await Promise.all([
      readFile(join(fontsDir, "SourceSans3-Regular.ttf")),
      readFile(join(fontsDir, "SourceSans3-Bold.ttf")),
      readFile(join(fontsDir, "SourceSans3-Semibold.ttf")),
    ]);

    const [regular, bold, semibold] = await Promise.all([
      pdfDoc.embedFont(regularBytes),
      pdfDoc.embedFont(boldBytes),
      pdfDoc.embedFont(semiboldBytes),
    ]);

    return { regular, bold, semibold, family: FONT_FAMILY, embedded: true };
  } catch {
    const regular = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const bold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
    return { regular, bold, semibold: bold, family: "Helvetica", embedded: false };
  }
}
