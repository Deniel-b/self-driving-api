import datetime

from PyCameraList.camera_device import test_list_cameras, list_video_devices, list_audio_devices
from PySide6.QtMultimedia import (QCamera, QImageCapture,
                                  QCameraDevice, QMediaCaptureSession,
                                  QMediaDevices)
import pprint

available_cameras = QMediaDevices.videoInputs()
print(available_cameras[0])

print(str(datetime.datetime.now()))