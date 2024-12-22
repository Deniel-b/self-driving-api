from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QComboBox
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QWidget

from PyCameraList.camera_device import list_video_devices

from Camera import CameraWidget


class MainWindow(QMainWindow):
    """
    Главное окно. Содержит CameraWidget, при показе запускаем камеру,
    при закрытии останавливаем.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Async camera example")

        self.camWidget = CameraWidget()
        self.setCentralWidget(self.camWidget)

    def showEvent(self, event):
        super().showEvent(event)
        self.camWidget.startCamera()

    def closeEvent(self, event):
        self.camWidget.stopCamera()
        super().closeEvent(event)

