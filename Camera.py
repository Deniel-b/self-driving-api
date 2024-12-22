import sys
import cv2
import numpy as np

from PySide6.QtCore import QThread, Signal, Slot, QObject, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from Reimage import ImageProcessor
import time


class CaptureWorker(QObject):
    rawFrameCaptured = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self.cap = None

    def startCapture(self):
        self.cap = cv2.VideoCapture(0)  # или (0, cv2.CAP_DSHOW) на Windows
        if not self.cap.isOpened():
            print("Не удалось открыть камеру!")
            return
        self._is_running = True

        while self._is_running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Отправляем кадр
            self.rawFrameCaptured.emit(frame)

            # "задержка" ~ 1 сек => 1 кадр/сек
            time.sleep(1)

        self.cap.release()

    def stopCapture(self):
        self._is_running = False


class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Два QLabel рядом, в HBox
        self.label_raw = QLabel("Raw")
        self.label_processed = QLabel("Processed")
        self.label_raw.setAlignment(Qt.AlignCenter)
        self.label_processed.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label_raw)
        layout.addWidget(self.label_processed)
        self.setLayout(layout)

        # Создаём объекты для захвата и обработки
        self.captureWorker = CaptureWorker()
        self.processorWorker = ImageProcessor()

        # И потоки под них
        self.captureThread = QThread()
        self.processorThread = QThread()

        # Переносим воркеров в потоки
        self.captureWorker.moveToThread(self.captureThread)
        self.processorWorker.moveToThread(self.processorThread)

        # Связываем сигналы/слоты
        # Когда captureThread стартует, worker начинает чтение камеры
        self.captureThread.started.connect(self.captureWorker.startCapture)

        # Сырый кадр (BGR) → сразу показываем (updateRawFrame) и отправляем на обработку
        self.captureWorker.rawFrameCaptured.connect(self.updateRawFrame)
        self.captureWorker.rawFrameCaptured.connect(self.processorWorker.processFrame)

        # Готовый обработанный (RGB) кадр → показываем справа
        self.processorWorker.processedFrame.connect(self.updateProcessedFrame)

    def startCamera(self):
        """Старт потоков (запуск захвата и обработки)."""
        self.captureThread.start()
        self.processorThread.start()

    def stopCamera(self):
        """Остановка захвата и завершение потоков."""
        # Сначала просим captureWorker остановиться
        self.captureWorker.stopCapture()

        # Завершаем поток захвата
        self.captureThread.quit()
        self.captureThread.wait()

        # Завершаем поток обработки (если там что-то крутится)
        self.processorThread.quit()
        self.processorThread.wait()

    @Slot(np.ndarray)
    def updateRawFrame(self, frame: np.ndarray):
        """
        Получаем "сырое" (BGR) изображение,
        конвертируем в RGB и выводим в левый QLabel.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytesPerLine = ch * w

        qimg = QImage(rgb_frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.label_raw.setPixmap(pixmap)

    @Slot(np.ndarray)
    def updateProcessedFrame(self, rgb_frame: np.ndarray):
        """Готовый (уже RGB) кадр выводим в правый QLabel."""
        h, w, ch = rgb_frame.shape
        bytesPerLine = ch * w

        qimg = QImage(rgb_frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.label_processed.setPixmap(pixmap)
