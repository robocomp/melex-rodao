import cv2
import numpy as np


class CameraManager(object):
    def __init__(self, mutex):
        self.images_received = {}
        self.mutex = mutex
        self.sensor_width = 360
        self.sensor_height = 280
        self.surface = None
        self.second_surface = None

    def convert_img(self):
        self.mutex.acquire()
        for camera_ID, camera_data in self.images_received.items():
            if camera_data is None:
                continue
            array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
            array = np.reshape(array, (camera_data.height, camera_data.width, 4))
            array = array[:, :, :3]

            window_name = "camera" + str(camera_ID)
            cv2.imshow(window_name, array)
            cv2.waitKey(1)
        self.mutex.release()

    def render(self):
        self.convert_img()

    def toggle_camera(self):
        print('toggle_camera')
        if self.id_camera_to_show == 5:
            self.id_camera_to_show = 7
        else:
            self.id_camera_to_show = 5
