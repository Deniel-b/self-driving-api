import time

import cv2
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, Slot, QObject, Qt, QTimer, QRunnable, QThreadPool
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QLabel, QWidget, QHBoxLayout
)

from Reimage import ImageProcessor


class CaptureWorker(QObject):
    """
    Отдельный поток для чтения кадров из камеры.
    """
    rawFrameCaptured = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self.cap = None

    def startCapture(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Не удалось открыть камеру!")
            return

        self._is_running = True
        while self._is_running:
            ret, frame = self.cap.read()
            if ret:
                self.rawFrameCaptured.emit(frame)
            time.sleep(0.5)

        self.cap.release()

    def stopCapture(self):
        self._is_running = False


class CameraWidget(QWidget):
    """
    Виджет:
      - Поток захвата (CaptureWorker + QThread),
      - Хранение "последнего кадра",
      - QTimer, чтобы раз в секунду обрабатывать кадр,
      - QThreadPool, куда мы "кидаем" задачи обработки (ProcessRunnable).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Два QLabel (слева "сырое", справа "обработанное")
        self.label_raw = QLabel("Raw")
        self.label_processed = QLabel("Processed")
        self.label_raw.setAlignment(Qt.AlignCenter)
        self.label_processed.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label_raw)
        layout.addWidget(self.label_processed)
        self.setLayout(layout)

        # Создаём поток для захвата
        self.captureWorker = CaptureWorker()
        self.captureThread = QThread()
        self.captureWorker.moveToThread(self.captureThread)

        # Когда поток запущен, worker начинает чтение
        self.captureThread.started.connect(self.captureWorker.startCapture)

        # Пришёл кадр -> сохраняем последний, параллельно показываем "сырое"
        self._lastFrame = None
        self.captureWorker.rawFrameCaptured.connect(self.storeFrame)

        # Обработчик (ваш ImageProcessor)
        self.processor = ImageProcessor()
        # Когда обработка готова -> показываем в правом QLabel
        self.processor.processedFrame.connect(self.updateProcessedFrame)

        # QThreadPool для запуска асинхронных задач
        self.threadPool = QThreadPool.globalInstance()

        # QTimer, чтобы не обрабатывать каждый кадр, а раз в секунду
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1 сек
        self.timer.timeout.connect(self.processLastFrame)
        self.timer.start()

    def startCamera(self):
        self.captureThread.start()

    def stopCamera(self):
        self.captureWorker.stopCapture()
        self.captureThread.quit()
        self.captureThread.wait()

    @Slot(np.ndarray)
    def storeFrame(self, frame):
        """Сохраняем последний кадр и показываем его в левом QLabel."""
        self._lastFrame = frame
        # Покажем "сырое" сразу
        self.updateRawFrame(frame)

    def processLastFrame(self):
        """
        Раз в секунду берём последний кадр и отправляем на обработку
        в пул потоков (через ProcessRunnable).
        """
        if self._lastFrame is not None:
            runnable = ProcessRunnable(self.processor, self._lastFrame)
            self.threadPool.start(runnable)

    @Slot(np.ndarray)
    def updateRawFrame(self, frame: np.ndarray):
        """Показ "сырое" (BGR -> RGB)."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytesPerLine = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.label_raw.setPixmap(QPixmap.fromImage(qimg))

    @Slot(np.ndarray)
    def updateProcessedFrame(self, frame_rgb: np.ndarray):
        """Готовый кадр (RGB) показываем в правом QLabel."""
        h, w, ch = frame_rgb.shape
        bytesPerLine = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.label_processed.setPixmap(QPixmap.fromImage(qimg))


class ProcessRunnable(QRunnable):
    """
    Класс-обёртка для запуска метода обработки (processor.processFrame)
    в пуле потоков (QThreadPool) без блокировки UI.
    """

    def __init__(self, processor, frame):
        super().__init__()
        self.processor = processor
        self.frame = frame

    def run(self):
        """
        Запускается в одном из потоков QThreadPool. Здесь мы просто
        вызываем метод обработки кадров. В нём (внутри ImageProcessor)
        уже есть сигнал processedFrame, который вернёт результат.
        """
        self.processor.processFrame(self.frame)
