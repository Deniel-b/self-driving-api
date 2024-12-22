from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QComboBox
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QWidget

from PyCameraList.camera_device import list_video_devices

from Camera import Camera

from Reimage import Reimage



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.firstCam
        # self.secondCam

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        menu_panel = QVBoxLayout()

        self.first_camera_list = QComboBox()
        for i in MainWindow.camera_list(self):
            self.first_camera_list.addItems(i)

        self.second_camera_list = QComboBox()
        for i in MainWindow.camera_list(self):
            self.second_camera_list.addItems(i)

        menu_panel.addWidget(self.first_camera_list)
        menu_panel.addWidget(self.second_camera_list)

        main_layout.addLayout(menu_panel)

        grid_layout = QGridLayout()

        # Вывод с первой камеры
        self.camera_1 = Camera()
        self.sink_ = Reimage(self.camera_1.viewfinder.videoSink())
        # self.label_camera_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.sink_, 0, 0)

        # Обработанное изображение с первой камеры
        # self.sink_ = Reimage(self.camera_1.viewfinder.videoSink())
        # grid_layout.addWidget(self.sink_, 0, 1)



        # Вывод со второй камеры
        self.label_camera_2 = QLabel("вывод с второй камеры")
        self.label_camera_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.label_camera_2, 1, 0)

        # Обработанное изображение со второй камеры
        self.label_processed_2 = QLabel("обработанное изображение с второй камеры")
        self.label_processed_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.label_processed_2, 1, 1)

        main_layout.addLayout(grid_layout)

    def camera_list(self):
        cameras = []
        for i in list_video_devices():
            cameras.append(list(i))

        return cameras

