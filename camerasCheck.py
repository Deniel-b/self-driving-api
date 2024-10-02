from PyCameraList.camera_device import test_list_cameras, list_video_devices, list_audio_devices


def camera_list(self):
    cameras = []
    for i in list_video_devices():
        cameras.append(list(i))


    return cameras
