#!/usr/bin/env python3
"""
Geo-reference PDF maps from the Input folder.

Workflow:
  1. Place PDF files in Input/.
  2. Add four corner coordinates per map to 'Decimal Coordinates.txt'.
  3. Run this script — each PDF opens for you to click the four map corners.
  4. GeoTIFFs are written to Output/ at full render resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import fitz
import numpy as np


def configure_proj_environment() -> None:
    """
    Force Python to use pyproj's PROJ database instead of PostGIS/PostgreSQL
    copies that are often found first on Windows and break CRS handling.
    """
    try:
        import pyproj.datadir

        proj_data = pyproj.datadir.get_data_dir()
    except ImportError:
        return

    if (Path(proj_data) / "proj.db").is_file():
        os.environ["PROJ_DATA"] = proj_data
        os.environ["PROJ_LIB"] = proj_data

    for var in ("PROJ_DATA", "PROJ_LIB"):
        current = os.environ.get(var, "")
        if "postgis" in current.lower() or "postgresql" in current.lower():
            os.environ[var] = proj_data


configure_proj_environment()

import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import Affine, array_bounds

from corner_picker import CORNER_NAMES, pick_corners
from image_enhance import estimate_native_dpi, upscale_image

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "Input"
OUTPUT_DIR = SCRIPT_DIR / "Output"
CACHE_DIR = SCRIPT_DIR / ".georef_cache"
COORDINATES_FILE = SCRIPT_DIR / "Decimal Coordinates.txt"

PDF_EXTENSIONS = {".pdf"}
DEFAULT_RENDER_DPI = 600
DISPLAY_MAX_WIDTH = 1800

QUALITY_PRESETS: dict[str, int | None] = {
    "draft": 300,
    "native": None,
    "standard": 600,
    "high": 900,
    "max": 1200,
}

# Embedded WGS84 definition avoids broken EPSG/PROJ database lookups on some PCs.
WGS84_CRS = CRS.from_wkt(
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'
)

CORNER_LINE_RE = re.compile(
    r"^\s*(?P<corner>[A-Za-z-]+)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)
EN_COORD_RE = re.compile(
    r"^\s*(?P<lon>\d+(?:\.\d+)?)\s*E\s*,?\s*(?P<lat>\d+(?:\.\d+)?)\s*N\s*$",
    re.IGNORECASE,
)

CORNER_ALIASES = {
    "top-left": "top-left",
    "topleft": "top-left",
    "top-right": "top-right",
    "topright": "top-right",
    "bottom-left": "bottom-left",
    "bottomleft": "bottom-left",
    "bottom-right": "bottom-right",
    "bottomright": "bottom-right",
}


def normalize_corner_name(raw: str) -> str:
    key = raw.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in key:
        key = key.replace("--", "-")
    compact = key.replace("-", "")
    if key in CORNER_ALIASES:
        return CORNER_ALIASES[key]
    if compact in CORNER_ALIASES:
        return CORNER_ALIASES[compact]
    raise ValueError(f"Unknown corner name: {raw!r}")


def parse_coordinate_value(raw: str) -> tuple[float, float]:
    """Parse '72.625 E 20.0 N', '72.625 E, 20.0 N', or '72.625 20.0' into (lon, lat)."""
    text = raw.strip()
    match = EN_COORD_RE.match(text)
    if match:
        return float(match.group("lon")), float(match.group("lat"))

    parts = text.replace(",", " ").split()
    if len(parts) == 4 and parts[1].upper() == "E" and parts[3].upper() == "N":
        return float(parts[0]), float(parts[2])
    if len(parts) == 2:
        return float(parts[0]), float(parts[1])

    raise ValueError(f"Could not parse coordinate: {raw!r}")


def load_coordinates_file(path: Path) -> dict[str, dict[str, tuple[float, float]]]:
    if not path.exists():
        raise FileNotFoundError(f"Coordinates file not found: {path}")

    entries: dict[str, dict[str, tuple[float, float]]] = {}
    current_name: str | None = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        corner_match = CORNER_LINE_RE.match(line)
        if corner_match:
            if current_name is None:
                raise ValueError(
                    f"{path.name}:{line_number}: corner line before image name: {line!r}"
                )
            corner = normalize_corner_name(corner_match.group("corner"))
            lon, lat = parse_coordinate_value(corner_match.group("value"))
            entries[current_name][corner] = (lon, lat)
            continue

        if current_name is not None:
            missing = [name for name in CORNER_NAMES if name not in entries[current_name]]
            if missing:
                raise ValueError(
                    f"{path.name}:{line_number}: '{current_name}' is missing corners: "
                    + ", ".join(missing)
                )

        current_name = line
        entries[current_name] = {}

    if current_name is not None:
        missing = [name for name in CORNER_NAMES if name not in entries[current_name]]
        if missing:
            raise ValueError(
                f"{path.name}: '{current_name}' is missing corners: " + ", ".join(missing)
            )

    if not entries:
        raise ValueError(f"No coordinate blocks found in {path.name}")

    return entries


def list_input_pdfs() -> list[Path]:
    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True)
        return []
    return [
        path
        for path in sorted(INPUT_DIR.iterdir())
        if path.is_file() and path.suffix.lower() in PDF_EXTENSIONS
    ]


def render_pdf_page(pdf_path: Path, dpi: int = DEFAULT_RENDER_DPI, page_index: int = 0) -> np.ndarray:
    """Render a PDF page to an RGB uint8 array at the requested DPI."""
    if dpi <= 0:
        raise ValueError(f"DPI must be positive, got {dpi}")

    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"{pdf_path.name}: page index {page_index} is out of range.")
        page = doc[page_index]
        pixmap = page.get_pixmap(
            dpi=dpi,
            alpha=False,
            colorspace=fitz.csRGB,
            annots=True,
        )

    array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
    return np.ascontiguousarray(array)


def scale_pixel_corners(
    pixel_corners: dict[str, tuple[float, float]],
    factor: float,
) -> dict[str, tuple[float, float]]:
    return {
        name: (col * factor, row * factor)
        for name, (col, row) in pixel_corners.items()
    }


def resolve_render_dpi(
    pdf_path: Path,
    quality: str,
    dpi_override: int | None,
) -> tuple[int, str]:
    if dpi_override is not None:
        return dpi_override, f"{dpi_override} DPI (manual)"

    preset = QUALITY_PRESETS.get(quality)
    if preset is None and quality == "native":
        native_dpi = estimate_native_dpi(pdf_path)
        return native_dpi, f"{native_dpi} DPI (native PDF image — no upscaling)"

    if preset is None:
        raise ValueError(f"Unknown quality preset: {quality!r}")

    return preset, f"{preset} DPI ({quality})"


def make_display_image(image: np.ndarray, max_width: int = DISPLAY_MAX_WIDTH) -> tuple[np.ndarray, float]:
    """Downsample for on-screen picking; return (display_image, scale_factor)."""
    height, width = image.shape[:2]
    if width <= max_width:
        return image, 1.0

    scale = max_width / width
    display_width = max_width
    display_height = max(1, int(round(height * scale)))

    try:
        from PIL import Image

        resized = Image.fromarray(image).resize((display_width, display_height), Image.Resampling.LANCZOS)
        return np.asarray(resized), width / display_width
    except ImportError:
        step = width / display_width
        rows = (np.arange(display_height) * (height / display_height)).astype(int)
        cols = (np.arange(display_width) * (width / display_width)).astype(int)
        return image[np.ix_(rows, cols)], step


def cache_path_for(pdf_path: Path, dpi: int) -> Path:
    return CACHE_DIR / f"{pdf_path.stem}_dpi{dpi}.json"


def save_corner_cache(
    cache_path: Path,
    pixel_corners: dict[str, tuple[float, float]],
    dpi: int,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "dpi": dpi,
        "corners": {name: [col, row] for name, (col, row) in pixel_corners.items()},
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_corner_cache(cache_path: Path) -> dict[str, tuple[float, float]] | None:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        corners = {
            name: (float(values[0]), float(values[1]))
            for name, values in payload["corners"].items()
        }
        missing = [name for name in CORNER_NAMES if name not in corners]
        if missing:
            return None
        return corners
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def load_corner_cache_for_dpi(
    pdf_path: Path,
    target_dpi: int,
) -> dict[str, tuple[float, float]] | None:
    """Load cached corners for this DPI, or scale them from the nearest cached DPI."""
    exact_path = cache_path_for(pdf_path, target_dpi)
    cached = load_corner_cache(exact_path)
    if cached is not None:
        print(f"Using saved corner clicks from {exact_path.name}")
        return cached

    if not CACHE_DIR.exists():
        return None

    best_corners: dict[str, tuple[float, float]] | None = None
    best_dpi: int | None = None
    for path in CACHE_DIR.glob(f"{pdf_path.stem}_dpi*.json"):
        match = re.search(r"_dpi(\d+)\.json$", path.name)
        if not match:
            continue
        source_dpi = int(match.group(1))
        corners = load_corner_cache(path)
        if corners is None:
            continue
        if best_dpi is None or abs(source_dpi - target_dpi) < abs(best_dpi - target_dpi):
            best_corners = corners
            best_dpi = source_dpi

    if best_corners is None or best_dpi is None:
        return None

    scale = target_dpi / best_dpi
    scaled = {
        name: (col * scale, row * scale)
        for name, (col, row) in best_corners.items()
    }
    print(f"Scaled corner clicks from {best_dpi} DPI to {target_dpi} DPI")
    save_corner_cache(exact_path, scaled, target_dpi)
    return scaled


def geographic_bounds(
    geo_corners: dict[str, tuple[float, float]],
) -> tuple[float, float, float, float]:
    """Return west, south, east, north from all corner coordinates."""
    lons = [geo_corners[name][0] for name in CORNER_NAMES]
    lats = [geo_corners[name][1] for name in CORNER_NAMES]
    west, east = min(lons), max(lons)
    south, north = min(lats), max(lats)
    return west, south, east, north


def pixel_bounds(
    pixel_corners: dict[str, tuple[float, float]],
) -> tuple[float, float, float, float]:
    """Return left, top, right, bottom row/col bounds from clicked corners."""
    cols = [pixel_corners[name][0] for name in CORNER_NAMES]
    rows = [pixel_corners[name][1] for name in CORNER_NAMES]
    return min(cols), min(rows), max(cols), max(rows)


def build_north_up_transform(
    left: float,
    top: float,
    right: float,
    bottom: float,
    west: float,
    south: float,
    east: float,
    north: float,
) -> Affine:
    """Map the clicked pixel rectangle to a north-up geographic bounding box."""
    width_px = right - left
    height_px = bottom - top
    if width_px <= 0 or height_px <= 0:
        raise ValueError("Clicked corners must span a non-zero area in the image.")

    pixel_width = (east - west) / width_px
    pixel_height = (north - south) / height_px
    return Affine(
        pixel_width,
        0.0,
        west - pixel_width * left,
        0.0,
        -pixel_height,
        north + pixel_height * top,
    )


def build_geotransform_from_corners(
    pixel_corners: dict[str, tuple[float, float]],
    geo_corners: dict[str, tuple[float, float]],
) -> tuple[Affine, str]:
    """
    Build an affine geotransform from clicked pixel locations and geographic corners.

    Pixel row 0 is the top of the rendered PDF page. The transform maps (col, row)
    to (longitude, latitude) without flipping the image.
    """
    design = []
    lon_targets = []
    lat_targets = []

    for name in CORNER_NAMES:
        col, row = pixel_corners[name]
        lon, lat = geo_corners[name]
        design.append([col, row, 1.0])
        lon_targets.append(lon)
        lat_targets.append(lat)

    matrix = np.array(design, dtype=float)
    lon_params = np.linalg.lstsq(matrix, np.array(lon_targets, dtype=float), rcond=None)[0]
    lat_params = np.linalg.lstsq(matrix, np.array(lat_targets, dtype=float), rcond=None)[0]

    transform = Affine(
        lon_params[0],
        lon_params[1],
        lon_params[2],
        lat_params[0],
        lat_params[1],
        lat_params[2],
    )

    residuals: list[float] = []
    for name in CORNER_NAMES:
        col, row = pixel_corners[name]
        lon, lat = geo_corners[name]
        mapped_lon = transform.a * col + transform.b * row + transform.c
        mapped_lat = transform.d * col + transform.e * row + transform.f
        residuals.append(abs(mapped_lon - lon))
        residuals.append(abs(mapped_lat - lat))

    max_residual = max(residuals)
    determinant = transform.a * transform.e - transform.b * transform.d
    unique_geo = len({geo_corners[name] for name in CORNER_NAMES})

    if abs(determinant) < 1e-12 or unique_geo < 4:
        west, south, east, north = geographic_bounds(geo_corners)
        left, top, right, bottom = pixel_bounds(pixel_corners)
        transform = build_north_up_transform(left, top, right, bottom, west, south, east, north)
        method = (
            "north-up bounding box (coordinates file has duplicate corner positions; "
            "using min/max lon/lat with your clicked map area)"
        )
        return transform, method

    fit_tolerance = 1e-3  # degrees (~100 m); exact fit is not always possible
    if max_residual > fit_tolerance:
        worst = max(
            CORNER_NAMES,
            key=lambda name: max(
                abs(
                    transform.a * pixel_corners[name][0]
                    + transform.b * pixel_corners[name][1]
                    + transform.c
                    - geo_corners[name][0]
                ),
                abs(
                    transform.d * pixel_corners[name][0]
                    + transform.e * pixel_corners[name][1]
                    + transform.f
                    - geo_corners[name][1]
                ),
            ),
        )
        raise ValueError(
            f"Transform fit error too large at {worst.replace('-', ' ')} "
            f"(max residual {max_residual:.6f} degrees)."
        )

    return transform, "affine fit from four ground control points"


def verify_geotiff(
    output_path: Path,
    expected_bounds: tuple[float, float, float, float],
    width: int,
    height: int,
) -> None:
    """Confirm the written GeoTIFF has usable geo metadata."""
    west, south, east, north = expected_bounds
    tolerance = 1e-6

    with rasterio.open(output_path) as dst:
        if dst.crs is None:
            raise ValueError(f"{output_path.name}: missing CRS")
        if dst.transform == Affine.identity():
            raise ValueError(f"{output_path.name}: missing geotransform")
        if dst.width != width or dst.height != height:
            raise ValueError(f"{output_path.name}: unexpected image size")

        bounds = dst.bounds
        if abs(bounds.left - west) > tolerance:
            raise ValueError(f"{output_path.name}: west bound mismatch")
        if abs(bounds.bottom - south) > tolerance:
            raise ValueError(f"{output_path.name}: south bound mismatch")
        if abs(bounds.right - east) > tolerance:
            raise ValueError(f"{output_path.name}: east bound mismatch")
        if abs(bounds.top - north) > tolerance:
            raise ValueError(f"{output_path.name}: north bound mismatch")


def write_geotiff(
    image: np.ndarray,
    transform: Affine,
    output_path: Path,
    source_name: str,
    *,
    compress: str = "deflate",
    build_overviews: bool = True,
) -> tuple[int, int, tuple[float, float, float, float]]:
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Expected an RGB image array.")

    height, width = image.shape[:2]
    data = np.transpose(image, (2, 0, 1))

    profile: dict = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 3,
        "dtype": data.dtype,
        "crs": WGS84_CRS,
        "transform": transform,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "interleave": "pixel",
        "photometric": "RGB",
        "BIGTIFF": "IF_SAFER",
    }

    if compress and compress.lower() != "none":
        profile["compress"] = compress
        if compress in {"deflate", "lzw", "zstd"}:
            profile["predictor"] = 2
        if compress == "deflate":
            profile["zlevel"] = 6

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data)
        dst.update_tags(
            AREA_OR_POINT="Area",
            GEoref_source=source_name,
            EPSG_code="4326",
        )
        if build_overviews:
            overview_levels = [
                factor
                for factor in (2, 4, 8, 16, 32, 64, 128)
                if min(width, height) // factor >= 256
            ]
            if overview_levels:
                dst.build_overviews(overview_levels, Resampling.average)
                dst.update_tags(ns="rio_overview", resampling="average")

    bounds = array_bounds(height, width, transform)
    verify_geotiff(output_path, bounds, width, height)
    return width, height, bounds


def format_corner_coords(corner_coords: dict[str, tuple[float, float]]) -> str:
    parts = []
    for name in CORNER_NAMES:
        lon, lat = corner_coords[name]
        label = name.replace("-", " ").title()
        parts.append(f"{label}: {lon} E, {lat} N")
    return " | ".join(parts)


def format_pixel_corners(pixel_corners: dict[str, tuple[float, float]]) -> str:
    parts = []
    for name in CORNER_NAMES:
        col, row = pixel_corners[name]
        label = name.replace("-", " ").title()
        parts.append(f"{label}: ({col:.1f}, {row:.1f})")
    return " | ".join(parts)


def format_bounds(bounds: tuple[float, float, float, float]) -> str:
    west, south, east, north = bounds
    return f"west={west}, south={south}, east={east}, north={north}"


def acquire_pixel_corners(
    pdf_path: Path,
    image: np.ndarray,
    dpi: int,
    reuse_cache: bool,
    force_pick: bool,
) -> dict[str, tuple[float, float]]:
    if not force_pick and reuse_cache:
        cached = load_corner_cache_for_dpi(pdf_path, dpi)
        if cached is not None:
            return cached

    display_image, scale_factor = make_display_image(image)
    print()
    print(f"Opening {pdf_path.name} for corner selection...")
    print("Click the four map corners in order: top-left, top-right, bottom-left, bottom-right.")
    print("Scroll or +/- to zoom, right-drag to pan, 0 to reset view.")
    print("Press R to reset corners, Enter to confirm when all four corners are set.")

    pixel_corners = pick_corners(
        display_image,
        title=pdf_path.name,
        scale_factor=scale_factor,
        on_complete=lambda corners: save_corner_cache(cache_path_for(pdf_path, dpi), corners, dpi),
    )
    return pixel_corners


def process_pdf(
    pdf_path: Path,
    geo_corners: dict[str, tuple[float, float]],
    quality: str,
    dpi_override: int | None,
    upscale_factor: int,
    reuse_cache: bool,
    force_pick: bool,
    compress: str,
    build_overviews: bool,
) -> None:
    render_dpi, render_label = resolve_render_dpi(pdf_path, quality, dpi_override)
    image = render_pdf_page(pdf_path, dpi=render_dpi)
    height, width = image.shape[:2]

    pixel_corners = acquire_pixel_corners(
        pdf_path,
        image,
        dpi=render_dpi,
        reuse_cache=reuse_cache,
        force_pick=force_pick,
    )

    upscale_label = ""
    if upscale_factor > 1:
        image = upscale_image(image, upscale_factor)
        pixel_corners = scale_pixel_corners(pixel_corners, upscale_factor)
        height, width = image.shape[:2]
        upscale_label = f" x{upscale_factor} AI upscale -> {render_dpi * upscale_factor} DPI effective"

    transform, transform_method = build_geotransform_from_corners(pixel_corners, geo_corners)
    output_path = OUTPUT_DIR / f"{pdf_path.stem}_georef.tif"

    print()
    print("=" * 60)
    print(f"PDF: {pdf_path.name}  (output {width} x {height} px)")
    print(f"Render quality: {render_label}{upscale_label}")
    print(f"Geo corners: {format_corner_coords(geo_corners)}")
    print(f"Pixel corners: {format_pixel_corners(pixel_corners)}")
    print(f"Georeferencing: {transform_method}")

    _, _, bounds = write_geotiff(
        image,
        transform,
        output_path,
        COORDINATES_FILE.name,
        compress=compress,
        build_overviews=build_overviews,
    )
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Output extent: {format_bounds(bounds)}")
    print(f"Saved and verified: {output_path} ({file_size_mb:.1f} MB)")


def parse_args(argv: list[str]) -> argparse.Namespace:
    preset_help = ", ".join(
        f"{name}={'auto' if value is None else value}"
        for name, value in QUALITY_PRESETS.items()
    )
    parser = argparse.ArgumentParser(
        description="Geo-reference PDF maps by clicking four corner points."
    )
    parser.add_argument(
        "--quality",
        choices=sorted(QUALITY_PRESETS),
        default="standard",
        help=f"Render quality preset ({preset_help}). Default: standard (600 DPI).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=None,
        help="Override render DPI (takes precedence over --quality).",
    )
    parser.add_argument(
        "--upscale",
        type=int,
        choices=(2, 4),
        default=None,
        help="AI super-resolution factor (2 or 4). Best with --quality native. Requires opencv-contrib-python.",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Write uncompressed GeoTIFF (largest files, marginally sharper).",
    )
    parser.add_argument(
        "--no-overviews",
        action="store_true",
        help="Skip internal image pyramids (not recommended for QGIS).",
    )
    parser.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Reuse saved corner clicks from .georef_cache/ when available.",
    )
    parser.add_argument(
        "--repick",
        action="store_true",
        help="Ignore cached corner clicks and open the picker again.",
    )
    parser.add_argument(
        "pdfs",
        nargs="*",
        help="Optional PDF file names or stems to process (defaults to all PDFs in Input/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.quality not in QUALITY_PRESETS:
        print(f"Error: Unknown quality preset: {args.quality!r}")
        return 1

    upscale_factor = args.upscale or 1
    compress = "none" if args.no_compress else "deflate"
    build_overviews = not args.no_overviews

    print("PDF Geo-Referencing Tool")
    print("-" * 24)
    print(f"Input folder      : {INPUT_DIR}")
    print(f"Output folder     : {OUTPUT_DIR}")
    print(f"Coordinates file  : {COORDINATES_FILE}")
    print(f"Quality preset    : {args.quality}")
    if args.dpi is not None:
        print(f"Render DPI        : {args.dpi} (manual override)")
    elif args.quality == "native":
        print("Render DPI        : native (auto-detected per PDF)")
    else:
        print(f"Render DPI        : {QUALITY_PRESETS[args.quality]}")
    if upscale_factor > 1:
        print(f"AI upscale        : x{upscale_factor}")
    print(f"GeoTIFF compress  : {compress}")
    print()

    try:
        coordinate_entries = load_coordinates_file(COORDINATES_FILE)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    pdfs = list_input_pdfs()
    if not pdfs:
        print("No PDF files found in the Input folder.")
        print(f"Add PDFs here: {INPUT_DIR}")
        return 1

    if args.pdfs:
        requested = set(args.pdfs)
        selected = []
        for pdf_path in pdfs:
            if pdf_path.name in requested or pdf_path.stem in requested:
                selected.append(pdf_path)
        missing = requested - {path.name for path in selected} - {path.stem for path in selected}
        if missing:
            print(f"Warning: no matching PDF for: {', '.join(sorted(missing))}")
        pdfs = selected

    if not pdfs:
        print("No matching PDF files to process.")
        return 1

    processed = 0
    reuse_cache = args.reuse_cache and not args.repick

    for pdf_path in pdfs:
        key = pdf_path.stem
        if key not in coordinate_entries:
            print(f"Skipping {pdf_path.name}: no block named '{key}' in coordinates file.")
            continue
        try:
            process_pdf(
                pdf_path,
                coordinate_entries[key],
                quality=args.quality,
                dpi_override=args.dpi,
                upscale_factor=upscale_factor,
                reuse_cache=reuse_cache,
                force_pick=args.repick,
                compress=compress,
                build_overviews=build_overviews,
            )
            processed += 1
        except (ValueError, RuntimeError) as exc:
            print(f"Failed {pdf_path.name}: {exc}")

    unused = sorted(set(coordinate_entries) - {path.stem for path in pdfs})
    if unused:
        print()
        print("Coordinate blocks with no matching PDF in Input:")
        for name in unused:
            print(f"  - {name}")

    if processed == 0:
        print()
        print("No PDFs were geo-referenced.")
        return 1

    print()
    print(f"Done. Geo-referenced {processed} PDF(s).")
    print("Run 'python check_georef.py' to inspect the output files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
