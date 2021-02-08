import numpy as np
import pygame
from multiprocessing import SimpleQueue
import cv2


class CameraManager(object):
    def __init__(self, width, height):

        self.current_image = None
        self.current_image_width = None
        self.current_image_height = None
        self.current_image_ID = None

        self.sensor_width = width
        self.sensor_height = height
        self.surface = None
        self.second_surface = None
        self.id_camera_to_show = 5
        self.second_width = 360
        self.sencond_height = 280
        # self.second_width = 1280
        # self.sencond_height = 720

    def update(self, image, width, height, cameraID):
        self.current_image = image
        self.current_image_width = width
        self.current_image_height = height
        self.current_image_ID = cameraID


    # def show_img(self, image, width, height, cameraID):
    def convert_img(self):
        array = np.frombuffer(self.current_image, dtype=np.dtype("uint8"))
        array = np.reshape(array, (self.current_image_height, self.current_image_width, 4))
        array = array[:, :, :3]
        # array = cv2.resize(array, dsize=(self.second_width, self.sencond_height))
        # window_name = "camera" + str(cameraID)
        # cv2.imshow(window_name, array)
        # cv2.waitKey(1)

        array_pygame = array[:, :, ::-1]

        if self.current_image_ID == self.id_camera_to_show:
            self.surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))
        else:

            array_pygame = cv2.resize(array_pygame, dsize=(self.second_width, self.sencond_height))
            self.second_surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))

    def render(self, display):
        self.convert_img()
        if self.surface is not None:
            display.blit(self.surface, (0, 0))
        if self.second_surface is not None:
            display.blit(self.second_surface, (self.sensor_width - self.second_width, self.sensor_height - self.sencond_height))

    def toggle_camera(self):
        print('toggle_camera')
        if self.id_camera_to_show == 5:
            self.id_camera_to_show = 6
        else:
            self.id_camera_to_show = 5


class GNSSSensor(object):
    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.frame = 0
        self.timestamp = 0
        self.gnss_queue = SimpleQueue()

    def update(self, lat, long, alt, frame, timestamp):
        self.latitude = lat
        self.longitude = long
        self.altitude = alt
        self.frame = frame
        self.timestamp = timestamp

        # print(f'self.latitude {self.latitude}')
        # print(f'self.longitude {self.longitude}')
        # print(f'self.altitude {self.altitude}')
        # print(f'self.frame {self.frame}')
        # print(f'self.timestamp {self.timestamp}')
        # self.gnss_queue.put()


class IMUSensor(object):
    def __init__(self):
        self.accelerometer = (0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.compass = 0.0
        self.frame = 0
        self.timestamp = 0
        # self.imu_queue = SimpleQueue()

    def update(self, acc, gyro, compass, frame, timestamp):
        self.accelerometer = acc
        self.gyroscope = gyro
        self.compass = compass
        self.frame = frame
        self.timestamp = timestamp
        # self.imu_queue.put(..)
