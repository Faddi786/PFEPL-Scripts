from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton,
    QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent, QColor
from PyQt6.QtCore import Qt, QPoint
import numpy as np

from utils.image_utils import numpy_to_qimage
from processing.color_detection import detect_colors
from processing.mask_generator import generate_mask
from file_io.tif_writer import save_mask


class MapViewer(QWidget):
    def __init__(self, image, profile):
        super().__init__()

        self.image = image
        self.profile = profile
        self.current_mask = None

        self.setWindowTitle("Map Extractor Viewer")
        self.resize(1000, 800)

        # --- Main label to display map ---
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.pixmap = QPixmap.fromImage(numpy_to_qimage(self.image))
        self.label.setPixmap(self.pixmap)
        self.label.setScaledContents(True)

        # --- Zoom / Pan variables ---
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.drag_start = None

        # --- Color buttons ---
        colors = detect_colors(self.image)
        self.color_buttons = []
        self.color_layout = QHBoxLayout()
        for c in colors:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            qcolor = QColor(int(c[0]), int(c[1]), int(c[2]))
            btn.setStyleSheet(f"background-color:{qcolor.name()}")
            btn.clicked.connect(lambda _, col=c: self.color_selected(col))
            self.color_layout.addWidget(btn)
            self.color_buttons.append(btn)

        # --- Save mask button ---
        self.save_btn = QPushButton("Save Mask")
        self.save_btn.clicked.connect(self.save_mask_file)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(self.color_layout)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

        # Enable mouse tracking for pixel color inspection
        self.label.setMouseTracking(True)
        self.label.mouseMoveEvent = self.show_pixel_color
        self.label.mousePressEvent = self.start_pan
        self.label.mouseReleaseEvent = self.end_pan
        self.label.mouseMoveEvent = self.do_pan
        self.label.wheelEvent = self.zoom_image

    # --- Color selection ---
    def color_selected(self, color):
        mask = generate_mask(self.image, np.array(color))
        self.current_mask = mask
        preview = self.image.copy()
        preview[mask == 0] = 0
        self.update_pixmap(preview)

    # --- Save mask ---
    def save_mask_file(self):
        if self.current_mask is None:
            QMessageBox.warning(self, "No mask", "Please select a color first.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Mask", "", "TIF Files (*.tif)")
        if file_path:
            save_mask(self.current_mask, self.profile, file_path)
            QMessageBox.information(self, "Saved", f"Mask saved to {file_path}")

    # --- Update display ---
    def update_pixmap(self, img):
        self.pixmap = QPixmap.fromImage(numpy_to_qimage(img))
        self.label.setPixmap(self.pixmap)

    # --- Pixel color inspector ---
    def show_pixel_color(self, event):
        x = int(event.position().x() / self.scale_factor - self.offset.x())
        y = int(event.position().y() / self.scale_factor - self.offset.y())
        if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
            r, g, b = self.image[y, x]
            self.setWindowTitle(f"Map Extractor Viewer - Pixel RGB: ({r},{g},{b})")

    # --- Zoom ---
    def zoom_image(self, event):
        delta = event.angleDelta().y()
        factor = 1.2 if delta > 0 else 0.8
        self.scale_factor *= factor
        self.label.resize(self.scale_factor * self.label.pixmap().size())

    # --- Pan ---
    def start_pan(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.position()

    def end_pan(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = None

    def do_pan(self, event: QMouseEvent):
        if self.drag_start is not None:
            diff = event.position() - self.drag_start
            self.label.move(self.label.pos() + diff.toPoint())
            self.drag_start = event.position()


# from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
# from PyQt6.QtGui import QPixmap
# import numpy as np

# from utils.image_utils import numpy_to_qimage
# from processing.color_detection import detect_colors
# from processing.mask_generator import generate_mask
# from ui.color_selector import ColorSelector

# class MapViewer(QWidget):

#     def __init__(self, image, profile):

#         super().__init__()

#         self.image = image
#         self.profile = profile

#         self.label = QLabel()

#         qimg = numpy_to_qimage(image)
#         self.label.setPixmap(QPixmap.fromImage(qimg))

#         colors = detect_colors(image)

#         self.selector = ColorSelector(colors, self.color_selected)

#         layout = QVBoxLayout()
#         layout.addWidget(self.label)
#         layout.addWidget(self.selector)

#         self.setLayout(layout)

#     def color_selected(self, color):

#         mask = generate_mask(self.image, np.array(color))

#         preview = self.image.copy()
#         preview[mask == 0] = 0

#         qimg = numpy_to_qimage(preview)

#         self.label.setPixmap(QPixmap.fromImage(qimg))