import numpy as np
import pygame
from multiprocessing import SimpleQueue
import cv2

class CameraManager(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = None
        self.second_surface = None
        self.id_camera_to_show = 5
        self.second_width = 360
        self.sencond_height = 280
        # self.second_width = 1280
        # self.sencond_height = 720

    def show_img(self, im):
        # im = self.data_queue.get()
        array = np.frombuffer(im.image, dtype=np.dtype("uint8"))
        array = np.reshape(array, (im.height, im.width, 4))
        array = array[:, :, :3]
        array = cv2.resize(array, dsize=(self.second_width, self.sencond_height))
        window_name = "camera" + str(im.cameraID)
        cv2.imshow(window_name, array)
        cv2.waitKey(1)

        # array_pygame = array[:, :, ::-1]
        #
        # if im.cameraID == self.id_camera_to_show:
        #     self.surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))
        # else:
        #
        #     array_pygame = cv2.resize(array_pygame, dsize = (self.second_width,self.sencond_height))
        #     self.second_surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))



    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))
        if self.second_surface is not None:
            display.blit(self.second_surface, (self.width-self.second_width, self.height-self.sencond_height))

    def toggle_camera(self):
        print('toggle_camera')
        if self.id_camera_to_show == 5:
            self.id_camera_to_show = 6
        else:
            self.id_camera_to_show = 5
