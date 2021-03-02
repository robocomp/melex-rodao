import cv2
import numpy as np
import pygame


class CameraManager(object):
    def __init__(self, width, height):
        self.images_received = {}
        self.current_image = None
        self.current_image_width = None
        self.current_image_height = None
        self.current_image_ID = None

        self.sensor_width = width
        self.sensor_height = height
        self.surface = None
        self.second_surface = None
        self.id_camera_to_show = 0
        self.id_second_camera_to_show = 1
        self.second_width = 360
        self.sencond_height = 280

    def update(self, image, width, height, cameraID):
        self.current_image = image
        self.current_image_width = width
        self.current_image_height = height
        self.current_image_ID = cameraID

    def convert_img(self):
        for camera_ID, camera_data in self.images_received.items():

            array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
            array = np.reshape(array, (camera_data.height, camera_data.width, 4))
            array = array[:, :, :3]

            if camera_ID == self.id_camera_to_show:
                array_pygame = array[:, :, ::-1]
                self.surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))
            elif camera_ID == self.id_second_camera_to_show:
                array_pygame = array[:, :, ::-1]
                array_pygame = cv2.resize(array_pygame, dsize=(self.second_width, self.sencond_height))
                self.second_surface = pygame.surfarray.make_surface(array_pygame.swapaxes(0, 1))
            else:
                array = cv2.resize(array, dsize=(self.second_width, self.sencond_height))
                window_name = "camera" + str(camera_ID)
                cv2.imshow(window_name, array)
                cv2.waitKey(1)

    def render(self, display):
        self.convert_img()
        if self.surface is not None:
            display.blit(self.surface, (0, 0))
        if self.second_surface is not None:
            display.blit(self.second_surface,
                         (self.sensor_width - self.second_width, self.sensor_height - self.sencond_height))

    def toggle_camera(self):
        print('toggle_camera')
        if self.id_camera_to_show == 0:
            self.id_camera_to_show = 1
        else:
            self.id_camera_to_show = 0


class GNSSSensor(object):
    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.frame = 0
        self.timestamp = 0

    def update(self, lat, long, alt, frame, timestamp):
        self.latitude = lat
        self.longitude = long
        self.altitude = alt
        self.frame = frame
        self.timestamp = timestamp


class IMUSensor(object):
    def __init__(self):
        self.accelerometer = (0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.compass = 0.0
        self.frame = 0
        self.timestamp = 0

    def update(self, acc, gyro, compass, frame, timestamp):
        self.accelerometer = acc
        self.gyroscope = gyro
        self.compass = compass
        self.frame = frame
        self.timestamp = timestamp
