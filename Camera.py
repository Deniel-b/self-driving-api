from PySide6.QtWidgets import (QWidget)
from PySide6.QtMultimedia import (QCamera, QMediaCaptureSession, QVideoSink, QCameraFormat,
                                  QImageCapture, QVideoFrame)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Slot, Signal, QObject


class Camera(QWidget):
    def __init__(self):
        super().__init__()

        self._format = QCameraFormat()
        self._format.minFrameRate = 1.0
        self._format.maxFrameRate = 5.0
        self._format.resolution = (1280, 720)

        self._capture_session = QMediaCaptureSession()
        self._camera = QCamera()
        self._camera.setCameraFormat(self._format)

        self._capture_session.setCamera(self._camera)

        self._image_capture = QImageCapture(self._camera)

        self.viewfinder = QVideoWidget()

        self._sink = QVideoSink()
        self._sink.connect(self.frame_changed, QVideoSink.videoFrameChanged)

        self._capture_session.setVideoSink(self._sink)
        self._capture_session.setVideoOutput(self.viewfinder)

        self.viewfinder.show()
        self._camera.start()

