#!/usr/bin/env python3
"""Native PDF resolution detection and AI super-resolution for map output."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import fitz
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent / ".models"

EDSR_MODEL_URLS = {
    2: "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x2.pb",
    4: "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb",
}


def estimate_native_dpi(pdf_path: Path, page_index: int = 0) -> int:
    """
    Estimate the highest DPI that does not upscale embedded PDF images.

    For scanned maps stored as JPEG inside the PDF, this is the real detail limit.
    """
    best = 72
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"{pdf_path.name}: page index {page_index} is out of range.")
        page = doc[page_index]
        for image in page.get_images(full=True):
            xref = image[0]
            info = doc.extract_image(xref)
            width_px = info["width"]
            height_px = info["height"]
            for rect in page.get_image_rects(xref):
                if rect.width <= 0 or rect.height <= 0:
                    continue
                dpi_x = width_px / (rect.width / 72.0)
                dpi_y = height_px / (rect.height / 72.0)
                best = max(best, int(min(dpi_x, dpi_y)))
    return best


def ensure_edsr_model(scale: int) -> Path:
    if scale not in EDSR_MODEL_URLS:
        raise ValueError(f"Upscale factor must be 2 or 4, got {scale}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / f"EDSR_x{scale}.pb"
    if model_path.exists():
        return model_path

    url = EDSR_MODEL_URLS[scale]
    print(f"Downloading EDSR x{scale} model (first run only)...")
    try:
        urllib.request.urlretrieve(url, model_path)
    except Exception as exc:
        raise RuntimeError(
            f"Could not download super-resolution model to {model_path}: {exc}"
        ) from exc
    return model_path


def upscale_image(
    image: np.ndarray,
    scale: int,
    tile_size: int = 384,
) -> np.ndarray:
    """
    Upscale an RGB image with EDSR super-resolution (tiled for large maps).

    This adds detail beyond the embedded PDF JPEG using AI enhancement.
    """
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "AI upscaling requires opencv-contrib-python. "
            "Install it with: pip install opencv-contrib-python"
        ) from exc

    if scale not in (2, 4):
        raise ValueError(f"Upscale factor must be 2 or 4, got {scale}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected an RGB image array.")

    model_path = ensure_edsr_model(scale)
    upsampler = cv2.dnn_superres.DnnSuperResImpl_create()
    upsampler.readModel(str(model_path))
    upsampler.setModel("edsr", scale)

    height, width = image.shape[:2]
    output = np.empty((height * scale, width * scale, 3), dtype=np.uint8)
    tile_size = max(64, tile_size)

    y_steps = list(range(0, height, tile_size))
    x_steps = list(range(0, width, tile_size))
    total_tiles = len(y_steps) * len(x_steps)
    done = 0

    print(f"AI upscaling x{scale} ({width} x {height} px) in {total_tiles} tiles...")

    for y0 in y_steps:
        y1 = min(y0 + tile_size, height)
        for x0 in x_steps:
            x1 = min(x0 + tile_size, width)
            tile = image[y0:y1, x0:x1]
            tile_bgr = cv2.cvtColor(tile, cv2.COLOR_RGB2BGR)
            upscaled_bgr = upsampler.upsample(tile_bgr)
            upscaled_rgb = cv2.cvtColor(upscaled_bgr, cv2.COLOR_BGR2RGB)

            oy0, ox0 = y0 * scale, x0 * scale
            oy1, ox1 = oy0 + upscaled_rgb.shape[0], ox0 + upscaled_rgb.shape[1]
            output[oy0:oy1, ox0:ox1] = upscaled_rgb

            done += 1
            if done == 1 or done == total_tiles or done % max(1, total_tiles // 10) == 0:
                print(f"  upscale progress: {done}/{total_tiles} tiles")

    return np.ascontiguousarray(output)
