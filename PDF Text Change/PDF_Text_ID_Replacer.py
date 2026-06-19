import fitz  # PyMuPDF
import os
import re


DEFAULT_OLD_TEXT = "DB_GM5505L"
DEFAULT_NEW_TEXT = "DB_GM5505L_2"
DEFAULT_OUTPUT_FOLDER = r"C:\Users\Swapnali\Desktop\PDF Output"

FONT_FILES = {
    "arial unicode ms": r"C:\Windows\Fonts\ARIALUNI.TTF",
    "arial": r"C:\Windows\Fonts\arial.ttf",
    "helvetica": r"C:\Windows\Fonts\arial.ttf",
    "timesnewroman": r"C:\Windows\Fonts\times.ttf",
    "times": r"C:\Windows\Fonts\times.ttf",
}

MIN_FONT_SIZE = 6.0
FONT_SCALE_STEP = 0.2
TEXT_PADDING = 1.5
TO_COLUMN_X_MIN = 170
TO_COLUMN_X_MAX = 200
TO_COLUMN_PADDING = 0.2
REDACT_EDGE_MARGIN = 0.5
TO_COLUMN_REDACT_MARGIN = 0.2
MIN_BORDER_HEIGHT = 10.0
MIN_BOUNDARY_OFFSET = 10.0
MAX_CELL_LINE_GAP = 8.0


def get_file_path(prompt):
    """Get an existing file path from user input."""
    path = input(prompt).strip().strip('"')

    if path.lower() == "done":
        return None

    while not os.path.exists(path):
        print(f"File not found: {path}")
        path = input(prompt).strip().strip('"')
        if path.lower() == "done":
            return None

    return path


def get_replacement_text(prompt, default_value):
    """Get replacement text, using default when user presses Enter."""
    value = input(f"{prompt} (press Enter for '{default_value}'): ").strip()
    return value or default_value


def get_output_folder(prompt, default_value):
    """Get output folder path, creating it if it does not exist."""
    value = input(f"{prompt} (press Enter for default): ").strip().strip('"')
    folder = value or default_value

    os.makedirs(folder, exist_ok=True)
    return folder


def build_output_path(pdf_path, output_folder, old_text, new_text):
    """Build output path in the chosen folder, updating the ID in the filename."""
    base_name = os.path.basename(pdf_path)
    name, ext = os.path.splitext(base_name)

    if old_text in name:
        updated_name = name.replace(old_text, new_text)
    else:
        updated_name = f"{name}_ID_Updated"

    return os.path.join(output_folder, f"{updated_name}{ext}")


def int_color_to_rgb(color):
    """Convert PyMuPDF span color to an RGB tuple."""
    return (
        ((color >> 16) & 255) / 255,
        ((color >> 8) & 255) / 255,
        (color & 255) / 255,
    )


def resolve_fontfile(font_name):
    """Map a PDF font name to a local TTF file."""
    normalized = (font_name or "").lower()
    for key, path in FONT_FILES.items():
        if key in normalized and os.path.exists(path):
            return path

    if os.path.exists(FONT_FILES["arial"]):
        return FONT_FILES["arial"]

    return None


def find_replacement_rects(page, old_text):
    """
    Find text rectangles for old_text, skipping values already updated
    (e.g. DB_GM5505L inside DB_GM5505L_2).
    """
    rects = []
    for rect in page.search_for(old_text):
        follow_rect = fitz.Rect(rect.x1, rect.y0, rect.x1 + 40, rect.y1)
        following = page.get_textbox(follow_rect).lstrip()

        if following.startswith("_2"):
            continue

        rects.append(rect)

    return rects


def get_span_for_rect(page, rect, old_text):
    """Find the full text span (sentence) that contains the matched rectangle."""
    best_span = None
    best_area = 0

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if old_text not in span.get("text", ""):
                    continue

                span_rect = fitz.Rect(span["bbox"])
                if not span_rect.intersects(rect):
                    continue

                overlap_area = (span_rect & rect).get_area()
                if overlap_area > best_area:
                    best_area = overlap_area
                    best_span = span

    return best_span


BOUNDARY_CLUSTER_TOLERANCE = 3.0


def cluster_boundaries(boundaries):
    """Merge nearby vertical line positions into a single column edge."""
    if not boundaries:
        return []

    clustered = []
    group = [boundaries[0]]

    for value in boundaries[1:]:
        if value - group[-1] <= BOUNDARY_CLUSTER_TOLERANCE:
            group.append(value)
        else:
            clustered.append(round(sum(group) / len(group), 1))
            group = [value]

    clustered.append(round(sum(group) / len(group), 1))
    return clustered


def get_vertical_boundaries(page, y0, y1):
    """Return tall vertical line x-positions that cross the given y-range."""
    boundaries = []

    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue

            p1, p2 = item[1], item[2]
            if abs(p1.x - p2.x) >= 1.5:
                continue

            line_y0 = min(p1.y, p2.y)
            line_y1 = max(p1.y, p2.y)
            line_height = line_y1 - line_y0
            if line_height < MIN_BORDER_HEIGHT:
                continue

            if line_y1 >= y0 and line_y0 <= y1:
                boundaries.append((p1.x + p2.x) / 2)

    return sorted({round(value, 1) for value in boundaries})


def get_page_column_boundaries(page):
    """Collect stable table column borders from the full page."""
    if getattr(page, "_column_boundaries", None) is not None:
        return page._column_boundaries

    boundaries = []
    page_rect = page.rect

    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue

            p1, p2 = item[1], item[2]
            if abs(p1.x - p2.x) >= 1.5:
                continue

            line_height = abs(p1.y - p2.y)
            if line_height < MIN_BORDER_HEIGHT:
                continue

            x_value = (p1.x + p2.x) / 2
            if 20 < x_value < page_rect.width - 20:
                boundaries.append(x_value)

    page._column_boundaries = cluster_boundaries(
        sorted({round(value, 1) for value in boundaries})
    )
    return page._column_boundaries


def get_row_adjacent_text_boundary(page, rect):
    """Find the nearest text in the next column on the same visual row."""
    y_mid = (rect.y0 + rect.y1) / 2
    best_x0 = None

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text or text == "\xa0":
                    continue

                span_rect = fitz.Rect(span["bbox"])
                if span_rect.x0 <= rect.x0 + 3:
                    continue

                span_y_mid = (span_rect.y0 + span_rect.y1) / 2
                if abs(span_y_mid - y_mid) > 4:
                    continue

                if best_x0 is None or span_rect.x0 < best_x0:
                    best_x0 = span_rect.x0

    if best_x0 is None:
        return None

    return best_x0 - TEXT_PADDING


def get_row_vertical_boundary(page, rect):
    """Find the column border from vertical table lines on this row."""
    row_boundaries = cluster_boundaries(get_vertical_boundaries(page, rect.y0, rect.y1))
    right_edges = [x for x in row_boundaries if x > rect.x0 + MIN_BOUNDARY_OFFSET]

    if not right_edges:
        return None

    after_span = [x for x in right_edges if x > rect.x1 - 2]
    if not after_span:
        return right_edges[-1]

    first_after = after_span[0]
    if (
        len(after_span) > 1
        and first_after - rect.x1 < 3
        and after_span[1] - first_after > 30
    ):
        return after_span[1]

    return first_after


def get_column_bounds(page, rect):
    """Return the left and right edges of the column that contains rect."""
    row_boundaries = cluster_boundaries(get_vertical_boundaries(page, rect.y0, rect.y1))
    page_boundaries = get_page_column_boundaries(page)
    boundaries = sorted(set(row_boundaries + page_boundaries))

    column_right = None
    for boundary in boundaries:
        if boundary > rect.x0 + 1:
            column_right = boundary
            break

    if column_right is None:
        return None, None

    column_left = None
    for boundary in reversed(boundaries):
        if boundary <= rect.x0 + 1:
            column_left = boundary
            break

    return column_left, column_right


def get_cell_right_boundary(page, rect):
    """Find the tightest valid right edge for the span's table cell."""
    row_vertical = get_row_vertical_boundary(page, rect)
    row_adjacent = get_row_adjacent_text_boundary(page, rect)

    if row_adjacent is not None and row_vertical is not None:
        if (
            rect.x0 < 120
            and row_vertical < row_adjacent
            and row_vertical - rect.x1 < 8
        ):
            return row_adjacent
        return min(row_vertical, row_adjacent)

    candidates = [value for value in (row_vertical, row_adjacent) if value is not None]

    if not candidates:
        page_boundaries = get_page_column_boundaries(page)
        page_after = [
            x
            for x in page_boundaries
            if x > rect.x0 + MIN_BOUNDARY_OFFSET and x > rect.x1 - 2
        ]
        if page_after:
            candidates.append(min(page_after))

    if not candidates:
        return None

    return min(candidates)


def is_to_column_keyword(keyword_rect, new_text):
    """Identify standalone IDs in the Baseline report To column."""
    return TO_COLUMN_X_MIN < keyword_rect.x0 < TO_COLUMN_X_MAX


def get_keyword_padding(keyword_rect):
    """Use tighter padding for the Baseline Processing Summary To column."""
    if is_to_column_keyword(keyword_rect, DEFAULT_NEW_TEXT):
        return TO_COLUMN_PADDING
    return TEXT_PADDING


def get_keyword_redact_margin(keyword_rect):
    """Keep To column keyword text inside its original slot."""
    if is_to_column_keyword(keyword_rect, DEFAULT_NEW_TEXT):
        return TO_COLUMN_REDACT_MARGIN
    return REDACT_EDGE_MARGIN


def get_keyword_max_width(page, keyword_rect):
    """Return the width available inside the keyword's table cell."""
    padding = get_keyword_padding(keyword_rect)
    cell_right = get_cell_right_boundary(page, keyword_rect)

    if is_to_column_keyword(keyword_rect, DEFAULT_NEW_TEXT) and cell_right is not None:
        return max(cell_right - keyword_rect.x0 - padding, MIN_FONT_SIZE)

    slot_width = keyword_rect.width - padding
    if cell_right is not None:
        cell_width = cell_right - keyword_rect.x0 - padding
        return max(min(slot_width, cell_width), MIN_FONT_SIZE)

    return max(slot_width, MIN_FONT_SIZE)


def measure_text_width(text, fontfile, font_size):
    """Measure rendered text width for a font file and size."""
    if fontfile:
        return fitz.Font(fontfile=fontfile).text_length(text, fontsize=font_size)

    return fitz.get_text_length(text, fontname="helv", fontsize=font_size)


def get_phrase_max_width(page, span_rect):
    """Return the width available for a phrase inside its original span box."""
    cell_right = get_cell_right_boundary(page, span_rect)
    span_width = span_rect.width - TEXT_PADDING

    if cell_right is not None:
        cell_width = cell_right - span_rect.x0 - TEXT_PADDING
        return max(min(span_width, cell_width), MIN_FONT_SIZE)

    return max(span_width, MIN_FONT_SIZE)


def build_phrase_redact_rect(span_rect, text_width, cell_right=None, redact_margin=REDACT_EDGE_MARGIN):
    """Erase the full original phrase area, capped to the cell edge."""
    right_edge = max(span_rect.x1, span_rect.x0 + text_width) + 1
    if cell_right is not None:
        right_edge = min(right_edge, cell_right - redact_margin)

    return fitz.Rect(
        span_rect.x0 - 0.5,
        span_rect.y0 - 0.5,
        right_edge + 0.5,
        span_rect.y1 + 0.5,
    )


def fit_text_font_size(text, fontfile, base_size, max_width):
    """Shrink font size until text fits inside the available width."""
    if not max_width:
        return base_size

    size = base_size

    while size > MIN_FONT_SIZE and measure_text_width(text, fontfile, size) > max_width:
        size -= FONT_SCALE_STEP

    return round(size, 2)


def build_keyword_redact_rect(
    keyword_rect,
    redact_margin=REDACT_EDGE_MARGIN,
    cell_right=None,
):
    """Erase only the original keyword area, capped to the cell edge."""
    right_edge = keyword_rect.x1 + redact_margin
    if cell_right is not None:
        right_edge = min(right_edge, cell_right - redact_margin)

    return fitz.Rect(
        keyword_rect.x0 - 0.5,
        keyword_rect.y0 - 0.5,
        right_edge,
        keyword_rect.y1 + 0.5,
    )


def calc_baseline(text_rect, font_size):
    """Vertically center replacement text inside the original keyword box."""
    return text_rect.y0 + (text_rect.height + font_size * 0.78) / 2


def find_span_block_line(page, span):
    """Locate the block and line index that contain a span."""
    span_bbox = tuple(round(value, 1) for value in span["bbox"])

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue

        for line_idx, line in enumerate(block["lines"]):
            for candidate in line["spans"]:
                if tuple(round(value, 1) for value in candidate["bbox"]) == span_bbox:
                    return block, line_idx

    return None, None


def get_column_lines_from_block(block, column_left, column_right):
    """Collect text lines that sit in the same table column within a block."""
    lines_info = []

    if column_left is None or column_right is None:
        return lines_info

    for line_idx, line in enumerate(block["lines"]):
        column_spans = [
            span
            for span in line["spans"]
            if column_left - 2 <= fitz.Rect(span["bbox"]).x0 < column_right - 2
        ]
        if not column_spans:
            continue

        line_rect = fitz.Rect(column_spans[0]["bbox"])
        for span in column_spans[1:]:
            line_rect |= fitz.Rect(span["bbox"])

        lines_info.append(
            {
                "line_idx": line_idx,
                "text": "".join(span["text"] for span in column_spans),
                "rect": line_rect,
                "font_name": column_spans[0]["font"],
                "font_size": column_spans[0]["size"],
                "color": column_spans[0]["color"],
            }
        )

    return lines_info


def has_horizontal_border_between(page, y0, y1):
    """Return True when a table row divider sits between two y positions."""
    if y1 <= y0:
        return False

    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue

            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) >= 1.5:
                continue

            if abs(p1.x - p2.x) < MIN_BORDER_HEIGHT:
                continue

            line_y = (p1.y + p2.y) / 2
            if y0 - 0.5 < line_y < y1 + 0.5:
                return True

    return False


def get_column_lines_in_same_cell(page, block, column_left, column_right, keyword_rect):
    """Collect only the lines that belong to the keyword's own table cell."""
    all_lines = get_column_lines_from_block(block, column_left, column_right)
    keyword_lines = [
        line_info
        for line_info in all_lines
        if line_info["rect"].intersects(keyword_rect)
    ]
    if not keyword_lines:
        return []

    keyword_line = keyword_lines[0]
    cell_lines = [keyword_line]
    sorted_lines = sorted(all_lines, key=lambda line: line["rect"].y0)

    try:
        keyword_index = sorted_lines.index(keyword_line)
    except ValueError:
        return cell_lines

    if keyword_index > 0:
        above = sorted_lines[keyword_index - 1]
        gap = keyword_line["rect"].y0 - above["rect"].y1
        if (
            gap <= MAX_CELL_LINE_GAP
            and not has_horizontal_border_between(
                page, above["rect"].y1, keyword_line["rect"].y0
            )
        ):
            cell_lines.insert(0, above)

    return cell_lines


def is_multiline_cell_group(page, block, column_left, column_right, keyword_rect):
    """Return True only for multiple lines inside the same table cell."""
    return (
        len(
            get_column_lines_in_same_cell(
                page, block, column_left, column_right, keyword_rect
            )
        )
        >= 2
    )


def get_group_style(line_infos, fallback_span):
    """Use the font style from the surrounding cell text."""
    for line_info in line_infos:
        if line_info.get("font_name"):
            return (
                line_info["font_name"],
                line_info["font_size"],
                line_info["color"],
            )

    return (
        fallback_span["font"],
        fallback_span["size"],
        fallback_span["color"],
    )


def union_rects(rects):
    """Return a rectangle that contains every input rectangle."""
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result |= fitz.Rect(rect)
    return result


def fit_lines_font_size(lines, fontfile, base_size, max_width):
    """Shrink font size until every line fits inside the available width."""
    if not max_width:
        return base_size

    size = base_size
    while size > MIN_FONT_SIZE:
        if all(
            measure_text_width(line["text"], fontfile, size) <= max_width
            for line in lines
        ):
            break
        size -= FONT_SCALE_STEP

    return round(size, 2)


def is_partial_keyword(span_rect, keyword_rect):
    """Return True when the keyword sits inside a larger single-line span."""
    return (
        keyword_rect.x0 > span_rect.x0 + 1
        or keyword_rect.x1 < span_rect.x1 - 1
    )


def build_multiline_redact_rect(line_rects, cell_right=None, redact_margin=REDACT_EDGE_MARGIN):
    """Erase the full multi-line cell phrase area."""
    redact_rect = union_rects(line_rects)
    if cell_right is not None:
        redact_rect.x1 = min(redact_rect.x1 + 0.5, cell_right - redact_margin)

    return fitz.Rect(
        redact_rect.x0 - 0.5,
        redact_rect.y0 - 0.5,
        redact_rect.x1 + 0.5,
        redact_rect.y1 + 0.5,
    )


def delete_links_in_rect(page, rect):
    """Remove every hyperlink annotation overlapping a rectangle."""
    for link in list(page.get_links()):
        link_rect = fitz.Rect(link["from"])
        if link_rect.intersects(rect):
            page.delete_link(link)


def delete_annotations_in_rect(page, rect):
    """Remove highlight and other annotations overlapping a rectangle."""
    for annot in list(page.annots() or []):
        if annot.rect.intersects(rect):
            page.delete_annot(annot)


def clear_interactive_markers_in_rect(page, rect):
    """Remove links and annotations that create viewer highlight boxes."""
    delete_links_in_rect(page, rect)
    delete_annotations_in_rect(page, rect)


def is_neutral_fill_color(color):
    """Return True for white/gray table backgrounds, not blue hyperlink pixels."""
    red, green, blue = color
    if blue > red + 0.06 and blue > green + 0.06:
        return False

    average = (red + green + blue) / 3
    if average > 0.9:
        return True

    channel_spread = max(abs(red - green), abs(green - blue), abs(red - blue))
    return 0.5 < average < 0.95 and channel_spread < 0.06


def sample_fill_color(page, rect):
    """Sample the table cell background, ignoring blue hyperlink text pixels."""
    clip = fitz.Rect(rect.x0 - 6, rect.y0 - 4, rect.x1 + 6, rect.y1 + 4)
    pixmap = page.get_pixmap(clip=clip, matrix=fitz.Matrix(4, 4))

    sample_points = [
        (clip.x0 + 2, clip.y0 + 2),
        (clip.x1 - 2, clip.y0 + 2),
        (clip.x0 + 2, clip.y1 - 2),
        (clip.x1 - 2, clip.y1 - 2),
        (clip.x0 + 2, clip.y0 + clip.height / 2),
        (clip.x1 - 2, clip.y0 + clip.height / 2),
    ]

    colors = []
    for point_x, point_y in sample_points:
        pixel_x = min(
            pixmap.width - 1,
            max(0, int((point_x - clip.x0) * 4)),
        )
        pixel_y = min(
            pixmap.height - 1,
            max(0, int((point_y - clip.y0) * 4)),
        )
        pixel = pixmap.pixel(pixel_x, pixel_y)
        if len(pixel) >= 3:
            colors.append(tuple(channel / 255 for channel in pixel[:3]))

    neutral_colors = [color for color in colors if is_neutral_fill_color(color)]
    if neutral_colors:
        return max(neutral_colors, key=lambda color: sum(color) / 3)

    return (1, 1, 1)


def collect_span_replacements(page, old_text, new_text):
    """
    Standalone keywords are fitted into their original keyword box.
    Multi-line cell phrases and single-line partial phrases are replaced
    as a whole and fitted into their original cell/span space.
    """
    replacements = []
    seen = set()

    for rect in find_replacement_rects(page, old_text):
        span = get_span_for_rect(page, rect, old_text)
        if span is None:
            continue

        keyword_rect = fitz.Rect(rect)
        span_rect = fitz.Rect(span["bbox"])
        block, _line_idx = find_span_block_line(page, span)
        column_left, column_right = get_column_bounds(page, keyword_rect)
        cell_right = column_right or get_cell_right_boundary(page, keyword_rect)
        multiline = (
            block is not None
            and column_left is not None
            and column_right is not None
            and is_multiline_cell_group(
                page, block, column_left, column_right, keyword_rect
            )
        )
        partial = is_partial_keyword(span_rect, keyword_rect)

        if multiline:
            match_key = (
                "cell",
                column_left,
                column_right,
                tuple(
                    round(value, 1)
                    for value in union_rects(
                        [
                            line_info["rect"]
                            for line_info in get_column_lines_in_same_cell(
                                page,
                                block,
                                column_left,
                                column_right,
                                keyword_rect,
                            )
                        ]
                    )
                ),
            )
        elif partial:
            match_key = ("phrase", tuple(round(value, 1) for value in span["bbox"]))
        else:
            match_key = ("keyword", tuple(round(value, 1) for value in keyword_rect))

        if match_key in seen:
            continue

        seen.add(match_key)

        if multiline:
            column_lines = get_column_lines_in_same_cell(
                page, block, column_left, column_right, keyword_rect
            )
            updated_lines = []
            for line_info in column_lines:
                updated_text = line_info["text"].replace(old_text, new_text)
                updated_lines.append(
                    {
                        "text": updated_text,
                        "rect": line_info["rect"],
                        "x0": line_info["rect"].x0,
                    }
                )

            font_name, base_font_size, span_color_int = get_group_style(
                column_lines, span
            )
            fontfile = resolve_fontfile(font_name)
            max_width = max(
                cell_right - updated_lines[0]["x0"] - TEXT_PADDING,
                MIN_FONT_SIZE,
            )
            font_size = fit_lines_font_size(
                updated_lines,
                fontfile,
                base_font_size,
                max_width,
            )
            for line in updated_lines:
                line["font_size"] = font_size
                line["text_width"] = measure_text_width(
                    line["text"], fontfile, font_size
                )
                line["baseline"] = calc_baseline(line["rect"], font_size)

            line_rects = [line["rect"] for line in updated_lines]
            redact_rect = build_multiline_redact_rect(
                line_rects,
                cell_right,
            )
            target_rect = union_rects(line_rects)

            replacements.append(
                {
                    "mode": "multiline",
                    "lines": updated_lines,
                    "redact_rect": redact_rect,
                    "font_name": font_name,
                    "font_size": font_size,
                    "color": int_color_to_rgb(span_color_int),
                    "color_int": span_color_int,
                    "fill": sample_fill_color(page, redact_rect),
                    "target_rect": target_rect,
                }
            )
            continue

        font_name = span["font"]
        base_font_size = span["size"]
        fontfile = resolve_fontfile(font_name)
        span_color_int = span["color"]

        if partial:
            phrase_text = span["text"].replace(old_text, new_text)
            if phrase_text == span["text"]:
                continue

            phrase_cell_right = get_cell_right_boundary(page, span_rect)
            max_width = get_phrase_max_width(page, span_rect)
            font_size = fit_text_font_size(
                phrase_text,
                fontfile,
                base_font_size,
                max_width,
            )
            text_width = measure_text_width(phrase_text, fontfile, font_size)
            redact_rect = build_phrase_redact_rect(
                span_rect,
                text_width,
                phrase_cell_right,
            )
            baseline = calc_baseline(span_rect, font_size)
            insert_point = (span_rect.x0, baseline)
            replacement_text = phrase_text
            target_rect = span_rect
            mode = "phrase"
        else:
            keyword_cell_right = get_cell_right_boundary(page, keyword_rect)
            max_width = get_keyword_max_width(page, keyword_rect)
            font_size = fit_text_font_size(
                new_text,
                fontfile,
                base_font_size,
                max_width,
            )
            text_width = measure_text_width(new_text, fontfile, font_size)
            redact_margin = get_keyword_redact_margin(keyword_rect)
            redact_rect = build_keyword_redact_rect(
                keyword_rect,
                redact_margin,
                keyword_cell_right,
            )
            baseline = calc_baseline(keyword_rect, font_size)
            insert_point = (keyword_rect.x0, baseline)
            replacement_text = new_text
            target_rect = keyword_rect
            mode = "keyword"

        replacements.append(
            {
                "mode": mode,
                "redact_rect": redact_rect,
                "insert_point": insert_point,
                "text": replacement_text,
                "text_width": text_width,
                "font_name": font_name,
                "font_size": font_size,
                "color": int_color_to_rgb(span_color_int),
                "color_int": span_color_int,
                "fill": sample_fill_color(page, redact_rect),
                "target_rect": target_rect,
            }
        )

    return replacements


def apply_replacement(page, replacement):
    """Insert replacement text using the matched local font style."""
    insert_kwargs = {
        "fontsize": replacement["font_size"],
        "color": replacement["color"],
    }

    fontfile = resolve_fontfile(replacement["font_name"])
    if fontfile:
        insert_kwargs["fontfile"] = fontfile
    else:
        insert_kwargs["fontname"] = "helv"

    if replacement.get("mode") == "multiline":
        for line in replacement["lines"]:
            page.insert_text(
                (line["x0"], line["baseline"]),
                line["text"],
                **insert_kwargs,
            )
    else:
        x0, baseline = replacement["insert_point"]
        page.insert_text(
            (x0, baseline),
            replacement["text"],
            **insert_kwargs,
        )


def replace_text_in_pdf(pdf_path, old_text, new_text, output_path):
    """Replace every occurrence of old_text with new_text across the PDF."""
    doc = fitz.open(pdf_path)
    total_replacements = 0
    pages_modified = []

    print(f"\nSearching for: {old_text}")
    print(f"Replacing with: {new_text}")
    print(f"Processing {len(doc)} page(s)...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        replacements = collect_span_replacements(page, old_text, new_text)

        if not replacements:
            continue

        for replacement in replacements:
            clear_interactive_markers_in_rect(page, replacement["redact_rect"])

        for replacement in replacements:
            page.add_redact_annot(
                replacement["redact_rect"],
                fill=replacement["fill"],
            )

        page.apply_redactions()

        for replacement in replacements:
            apply_replacement(page, replacement)
            clear_interactive_markers_in_rect(page, replacement["redact_rect"])

        total_replacements += len(replacements)
        pages_modified.append(page_num + 1)
        print(f"   Page {page_num + 1}: {len(replacements)} replacement(s)")

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

    return total_replacements, pages_modified


def count_remaining_matches(pdf_path, old_text):
    """Count remaining old_text values that are not already updated."""
    pattern = re.compile(re.escape(old_text) + r"(?!_2)")
    doc = fitz.open(pdf_path)
    count = sum(len(pattern.findall(page.get_text())) for page in doc)
    doc.close()
    return count


def process_single_pdf(pdf_path, output_folder, old_text, new_text):
    """Process one PDF and return a result summary."""
    output_path = build_output_path(pdf_path, output_folder, old_text, new_text)

    print(f"\n{'=' * 60}")
    print(f"Input PDF:    {os.path.basename(pdf_path)}")
    print(f"Output PDF:   {os.path.basename(output_path)}")
    print(f"Output folder: {output_folder}")
    print(f"{'=' * 60}")

    total_replacements, pages_modified = replace_text_in_pdf(
        pdf_path, old_text, new_text, output_path
    )

    remaining = count_remaining_matches(output_path, old_text)

    return {
        "input": os.path.basename(pdf_path),
        "output": output_path,
        "replacements": total_replacements,
        "pages_modified": pages_modified,
        "remaining": remaining,
    }


def main():
    print("=" * 70)
    print("PDF TEXT ID REPLACER")
    print("=" * 70)
    print("\nReplaces an ID/text value everywhere it appears in PDF text.")
    print("Multi-line cell phrases, single-line phrases, and standalone keywords are handled separately.")
    print(f"Default change: {DEFAULT_OLD_TEXT} -> {DEFAULT_NEW_TEXT}")
    print("Enter 'done' at the PDF prompt to finish.\n")

    old_text = get_replacement_text("Enter text to search for", DEFAULT_OLD_TEXT)
    new_text = get_replacement_text("Enter replacement text", DEFAULT_NEW_TEXT)

    if old_text == new_text:
        print("\nSearch text and replacement text are the same. Exiting.")
        return

    output_folder = get_output_folder(
        f"Enter output folder [{DEFAULT_OUTPUT_FOLDER}]",
        DEFAULT_OUTPUT_FOLDER,
    )
    print(f"\nOutput folder: {output_folder}")

    processed_files = []

    while True:
        pdf_path = get_file_path("\nEnter PDF file path: ")
        if pdf_path is None:
            break

        try:
            result = process_single_pdf(pdf_path, output_folder, old_text, new_text)
            processed_files.append(result)

            print(f"\n{'=' * 60}")
            if result["replacements"] > 0:
                print("SUCCESS")
                print(f"   Total replacements: {result['replacements']}")
                print(f"   Pages modified: {result['pages_modified']}")
                print(f"   Remaining matches: {result['remaining']}")
                print(f"   Output saved as: {result['output']}")
            else:
                print(f"No matches found for '{old_text}'")
                print("   No changes were made.")
            print(f"{'=' * 60}")

        except Exception as e:
            print(f"\nError processing {pdf_path}: {e}")
            import traceback

            traceback.print_exc()
            print("Skipping this file...")

    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)

    if processed_files:
        print(f"\nProcessed {len(processed_files)} PDF(s):\n")
        for index, result in enumerate(processed_files, 1):
            print(f"{index}. Input:  {result['input']}")
            print(f"   Output: {result['output']}")
            print(f"   Replacements: {result['replacements']}")
            print(f"   Pages modified: {result['pages_modified']}\n")
    else:
        print("\nNo files were processed.")

    print("=" * 70)


if __name__ == "__main__":
    main()
