import sys

from PySide6.QtWidgets import QApplication
from MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    available_geometry = window.screen().availableGeometry()
    window.resize(available_geometry.width() / 1.2, available_geometry.height() / 1.2)
    window.show()

    sys.exit(app.exec_())
