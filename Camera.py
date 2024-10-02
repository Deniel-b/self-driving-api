import os
import sys
from PySide6.QtCore import QDate, QDir, QStandardPaths, Qt, QUrl, Slot
from PySide6.QtGui import QAction, QGuiApplication, QDesktopServices, QIcon
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QTabWidget, QToolBar, QVBoxLayout, QWidget)
from PySide6.QtMultimedia import (QCamera, QImageCapture,
                                  QCameraDevice, QMediaCaptureSession,
                                  QMediaDevices)
from PySide6.QtMultimediaWidgets import QVideoWidget


class Camera(QWidget):
    def __init__(self, previewImage, fileName):
        super().__init__()

        self.file_name = fileName

        main_layout = QVBoxLayout(self)
        self._image_label = QLabel
        self._image_label.setPixmap(QPixmap.fromImage(previewImage))
        main_layout.addWidget(self._image_label)

        top_layout = QHBoxLayout()
        self._file_name_label = QLabel(QDir.toNativeSeparators(fileName))
        self._file_name_label.setTextInteractionFlags(Qt.TextBrowserInteraction)