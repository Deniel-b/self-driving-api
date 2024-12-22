import sys
import cv2
import numpy as np

from PySide6.QtCore import QThread, Signal, Slot, QObject, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout
)


class CameraWorker(QObject):
    """
    Worker, который непрерывно читает кадры из OpenCV-камеры (cv2.VideoCapture)
    и отправляет сигнал с numpy-массивом.
    """
    frameCaptured = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self.cap = None

        # Примерные настройки для уменьшения нагрузки
        self._sigma = 10            # "сила" размытия
        self._resize_factor = 2     # уменьшаем кадр в 2 раза перед обработкой

    def startCamera(self):
        """Запускается, когда поток (QThread) стартовал."""
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Для Windows: CV_CAP_DSHOW
        # Или просто: cv2.VideoCapture(0) — зависит от платформы
        if not self.cap.isOpened():
            print("Не удалось открыть камеру!")
            return

        self._is_running = True
        while self._is_running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Пример: GaussianBlur + resize
            h, w = frame.shape[:2]
            small_frame = cv2.resize(
                frame, (w // self._resize_factor, h // self._resize_factor)
            )
            blurred_small = cv2.GaussianBlur(small_frame, (0, 0), self._sigma)
            blurred = cv2.resize(blurred_small, (w, h))

            # BGR -> RGB
            blurred_rgb = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)

            # Отправляем кадр в основной поток
            self.frameCaptured.emit(blurred_rgb)

        self.cap.release()

    def stopCamera(self):
        """Останавливает цикл while и закрывает камеру."""
        self._is_running = False


class CameraWidget(QWidget):
    """
    Виджет, внутри которого:
      - QLabel для показа текущего кадра,
      - Worker (CameraWorker) и QThread для захвата и обработки.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Простейшая верстка: лейбл в вертикальном лей-ауте
        self.label = QLabel("No feed")
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Создаём объекты для работы с камерой
        self.worker = CameraWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Когда поток запускается, worker начинает читать камеру
        self.thread.started.connect(self.worker.startCamera)
        # При остановке приложения — аккуратно всё закрываем
        # (или можем вызвать stopCamera() из MainWindow)

        # При получении нового кадра обновляем изображение
        self.worker.frameCaptured.connect(self.updateImage)

    def startCamera(self):
        """Старт потока (и, соответственно, startCamera() в worker)."""
        self.thread.start()

    def stopCamera(self):
        """Останавливаем камеру, завершаем поток."""
        self.worker.stopCamera()
        self.thread.quit()
        self.thread.wait()

    @Slot(np.ndarray)
    def updateImage(self, frame: np.ndarray):
        """
        Слот, в который приходит обработанный кадр (numpy array).
        Конвертируем в QPixmap и отображаем в QLabel.
        """
        h, w, ch = frame.shape
        bytesPerLine = ch * w
        qimg = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)