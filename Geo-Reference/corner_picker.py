#!/usr/bin/env python3
"""Interactive corner-point picker for geo-referencing."""

from __future__ import annotations

from typing import Callable

import matplotlib.pyplot as plt
import numpy as np

CORNER_NAMES = ("top-left", "top-right", "bottom-left", "bottom-right")

CORNER_LABELS = {
    "top-left": "Top-Left",
    "top-right": "Top-Right",
    "bottom-left": "Bottom-Left",
    "bottom-right": "Bottom-Right",
}

ZOOM_FACTOR = 1.25
MIN_VIEW_PX = 40


def pick_corners(
    image: np.ndarray,
    title: str,
    scale_factor: float = 1.0,
    on_complete: Callable[[dict[str, tuple[float, float]]], None] | None = None,
) -> dict[str, tuple[float, float]]:
    """
    Let the user click the four map corners on a displayed image.

    Returns pixel corners as {corner_name: (col, row)} in full-resolution
    coordinates (scaled by scale_factor when display is downsampled).
    """
    if image.ndim == 2:
        display = image
    elif image.shape[2] >= 3:
        display = image[:, :, :3]
    else:
        display = image[:, :, 0]

    height, width = display.shape[:2]
    corners: dict[str, tuple[float, float]] = {}
    markers: list = []
    texts: list = []
    step = 0
    pan_state: dict[str, object] | None = None

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.imshow(display, interpolation="nearest", origin="upper")
    ax.set_axis_off()

    full_xlim = ax.get_xlim()
    full_ylim = ax.get_ylim()
    ylim_descending = full_ylim[0] > full_ylim[1]

    status = fig.text(
        0.5,
        0.02,
        "",
        ha="center",
        va="bottom",
        fontsize=11,
        transform=fig.transFigure,
    )

    def view_size() -> tuple[float, float, float, float]:
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        width_view = abs(xlim[1] - xlim[0])
        height_view = abs(ylim[1] - ylim[0])
        center_x = (xlim[0] + xlim[1]) / 2
        center_y = (ylim[0] + ylim[1]) / 2
        return center_x, center_y, width_view, height_view

    def make_ylim(center_y: float, height_view: float) -> tuple[float, float]:
        half_h = height_view / 2
        if ylim_descending:
            return (center_y + half_h, center_y - half_h)
        return (center_y - half_h, center_y + half_h)

    def update_status() -> None:
        controls = (
            "Scroll or +/- to zoom | Right-drag to pan | 0 to reset view | "
            "R to reset corners | Enter to confirm"
        )
        if step < len(CORNER_NAMES):
            name = CORNER_NAMES[step]
            status.set_text(
                f"{title} — Click {CORNER_LABELS[name]} ({step + 1}/4).  {controls}"
            )
        else:
            status.set_text(f"{title} — All corners selected.  {controls}")
        fig.canvas.draw_idle()

    def clamp_limits(
        xlim: tuple[float, float],
        ylim: tuple[float, float],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        view_w = abs(xlim[1] - xlim[0])
        view_h = abs(ylim[1] - ylim[0])
        max_w = abs(full_xlim[1] - full_xlim[0])
        max_h = abs(full_ylim[1] - full_ylim[0])

        view_w = max(MIN_VIEW_PX, min(view_w, max_w))
        view_h = max(MIN_VIEW_PX, min(view_h, max_h))

        cx = (xlim[0] + xlim[1]) / 2
        cy = (ylim[0] + ylim[1]) / 2

        half_w = view_w / 2
        half_h = view_h / 2

        min_cx = full_xlim[0] + half_w
        max_cx = full_xlim[1] - half_w
        min_cy = min(full_ylim[0], full_ylim[1]) + half_h
        max_cy = max(full_ylim[0], full_ylim[1]) - half_h

        if min_cx <= max_cx:
            cx = min(max(cx, min_cx), max_cx)
        else:
            cx = (full_xlim[0] + full_xlim[1]) / 2
            half_w = max_w / 2

        if min_cy <= max_cy:
            cy = min(max(cy, min_cy), max_cy)
        else:
            cy = (full_ylim[0] + full_ylim[1]) / 2
            half_h = max_h / 2

        return (cx - half_w, cx + half_w), make_ylim(cy, view_h)

    def set_view(xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
        xlim, ylim = clamp_limits(xlim, ylim)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        fig.canvas.draw_idle()

    def reset_view() -> None:
        set_view(full_xlim, full_ylim)

    def zoom_at(center_x: float, center_y: float, factor: float) -> None:
        _, _, width_view, height_view = view_size()
        width_view /= factor
        height_view /= factor
        new_xlim = (center_x - width_view / 2, center_x + width_view / 2)
        new_ylim = make_ylim(center_y, height_view)
        set_view(new_xlim, new_ylim)

    def zoom_center(factor: float) -> None:
        center_x, center_y, _, _ = view_size()
        zoom_at(center_x, center_y, factor)

    def reset_corners() -> None:
        nonlocal step
        corners.clear()
        step = 0
        for marker in markers:
            marker.remove()
        markers.clear()
        for text in texts:
            text.remove()
        texts.clear()
        update_status()

    def on_click(event) -> None:
        nonlocal step, pan_state
        if event.inaxes is not ax:
            return

        if event.button == 3:
            if event.xdata is not None and event.ydata is not None:
                pan_state = {
                    "x": event.xdata,
                    "y": event.ydata,
                    "xlim": ax.get_xlim(),
                    "ylim": ax.get_ylim(),
                }
            return

        if event.button != 1 or step >= len(CORNER_NAMES):
            return
        if event.xdata is None or event.ydata is None:
            return

        name = CORNER_NAMES[step]
        col = float(event.xdata) * scale_factor
        row = float(event.ydata) * scale_factor
        corners[name] = (col, row)

        marker = ax.plot(
            event.xdata,
            event.ydata,
            "o",
            color="red",
            markersize=8,
            markeredgecolor="white",
            markeredgewidth=1.5,
        )[0]
        markers.append(marker)

        label = ax.text(
            event.xdata + 8,
            event.ydata - 8,
            CORNER_LABELS[name],
            color="yellow",
            fontsize=9,
            fontweight="bold",
            bbox={"facecolor": "black", "alpha": 0.6, "pad": 2},
        )
        texts.append(label)

        step += 1
        update_status()

    def on_motion(event) -> None:
        if pan_state is None or event.inaxes is not ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        dx = event.xdata - pan_state["x"]
        dy = event.ydata - pan_state["y"]
        xlim = pan_state["xlim"]
        ylim = pan_state["ylim"]
        set_view((xlim[0] - dx, xlim[1] - dx), (ylim[0] - dy, ylim[1] - dy))

    def on_release(event) -> None:
        nonlocal pan_state
        if event.button == 3:
            pan_state = None

    def on_scroll(event) -> None:
        if event.inaxes is not ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        if event.button == "up":
            zoom_at(event.xdata, event.ydata, ZOOM_FACTOR)
        elif event.button == "down":
            zoom_at(event.xdata, event.ydata, 1 / ZOOM_FACTOR)

    def on_key(event) -> None:
        if event.key in ("r", "R"):
            reset_corners()
        elif event.key in ("0", "home"):
            reset_view()
        elif event.key in ("+", "=", "add"):
            zoom_center(ZOOM_FACTOR)
        elif event.key in ("-", "_", "subtract"):
            zoom_center(1 / ZOOM_FACTOR)
        elif event.key in ("enter", "return") and len(corners) == 4:
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    fig.canvas.mpl_connect("key_press_event", on_key)

    update_status()
    plt.tight_layout()
    plt.show()

    if len(corners) != 4:
        raise RuntimeError("Corner picking was cancelled before all four corners were set.")

    if on_complete is not None:
        on_complete(corners)

    return corners
