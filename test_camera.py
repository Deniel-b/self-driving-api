import cv2  # type: ignore
from cv2PySide6 import FrameToArrayConverter, NDArrayLabel
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, Qt, QThread
from PySide6.QtMultimedia import QMediaCaptureSession, QVideoSink, QVideoFrame, QCamera
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtMultimediaWidgets import QVideoWidget
from Camera import Camera

from depth_anything.dpt import DepthAnything
from depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet

import torch
import torch.nn.functional as F
from torchvision.transforms import Compose


class Reimage(QVideoWidget):
    def __init__(self, sink_: QVideoSink):
        super().__init__()

        self._capture_session = QMediaCaptureSession()
        self._image = sink_
        self._image.videoFrameChanged.connect(self.on_frame_changed)

    def on_frame_changed(self, frame: QVideoFrame):
        if not frame.isValid():
            return
        if not frame.map(frame.MapMode.ReadOnly):
            return

        frame.unmap()
        self._capture_session.setImageCapture(frame)


