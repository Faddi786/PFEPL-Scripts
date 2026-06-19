import sys
from PyQt6.QtWidgets import QApplication, QFileDialog
from ui.viewer import MapViewer
from file_io.tif_loader import load_tif

def main():

    app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Open Map",
        "",
        "TIF Files (*.tif *.tiff)"
    )

    if not file_path:
        return

    image, profile = load_tif(file_path)

    viewer = MapViewer(image, profile)
    viewer.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()