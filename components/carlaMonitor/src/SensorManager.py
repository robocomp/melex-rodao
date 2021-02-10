import numpy as np
import pygame
from multiprocessing import SimpleQueue
import cv2
from threading import Lock


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

            array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
            array = np.reshape(array, (camera_data.height, camera_data.width, 4))
            array = array[:, :, :3]

            # if camera_ID == self.id_camera_to_show:
            #     array_pygame = array[:, :, ::-1]
            #     self.surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))

            # array = cv2.resize(array, dsize=(self.sensor_width, self.sensor_height))
            window_name = "camera" + str(camera_ID)
            cv2.imshow(window_name, array)
            cv2.waitKey(1)
        self.mutex.release()

    # def render(self, display):
    def render(self):
        self.convert_img()
        # if self.surface is not None:
        #     display.blit(self.surface, (0, 0))
        # if self.second_surface is not None:
        #     display.blit(self.second_surface,
        #                  (self.sensor_width - self.second_width, self.sensor_height - self.sencond_height))

    def toggle_camera(self):
        print('toggle_camera')
        if self.id_camera_to_show == 5:
            self.id_camera_to_show = 7
        else:
            self.id_camera_to_show = 5

