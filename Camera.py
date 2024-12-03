from PySide6.QtWidgets import (QWidget)
from PySide6.QtMultimedia import (QCamera, QMediaCaptureSession, QMediaDevices, QVideoSink)
from PySide6.QtMultimediaWidgets import QVideoWidget


class Camera(QWidget):
    def __init__(self):
        super().__init__()

        self._capture_session = QMediaCaptureSession()
        self._camera = QCamera()
        self._capture_session.setCamera(self._camera)
        self.viewfinder = QVideoWidget()
        self._capture_session.setVideoOutput(self.viewfinder)
        self.viewfinder.show()
        self._camera.start()
