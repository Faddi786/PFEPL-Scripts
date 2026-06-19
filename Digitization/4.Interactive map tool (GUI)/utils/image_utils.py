from PyQt6.QtGui import QImage
import numpy as np

def numpy_to_qimage(img):

    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    height, width, channel = img.shape

    bytes_per_line = channel * width

    qimg = QImage(
        img.tobytes(),
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888
    )

    return qimg