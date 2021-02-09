import time
import weakref
from multiprocessing import SimpleQueue
from threading import Lock

import RoboCompCameraRGBDSimple
import carla
import cv2
import numpy as np
import pygame
from carla import ColorConverter as cc

mutex = Lock()


# # ==============================================================================
# # -- CameraManager -------------------------------------------------------------
# # ==============================================================================

class CameraManager(object):
    def __init__(self, world, bp_library, camerargbdsimplepub_proxy):
        self.surface = None
        self.contFPS = 0
        self.start = time.time()
        self.sensor_width = 360
        self.sensor_height = 280
        self.camerargbdsimplepub_proxy = camerargbdsimplepub_proxy

        self.blueprint_library = bp_library

        self.sensor_list = []
        self.cm_queue = SimpleQueue()
        weak_self = weakref.ref(self)
        self._cc = {
            '000': cc.Raw,
            '001': cc.Raw,
            '002': cc.Raw,
            '003': cc.Raw,
            '004': cc.Raw,
            '005': cc.Raw,
            '006': cc.Raw
        }

        cam_bp = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        cam_bp.set_attribute('fov', '110')
        cam_bp.set_attribute('sensor_tick', '5.0')

        # for attr in cam_bp_low:
        #     print('  - {}'.format(attr))

        ###################
        # STREET SENSORS ##
        ###################

        lmanager = world.get_lightmanager()
        mylights = lmanager.get_all_lights()

        spawn_point_8 = carla.Transform(
            carla.Location(x=mylights[8].location.x, z=mylights[8].location.z + 5, y=mylights[8].location.y),
            carla.Rotation(pitch=-15, yaw=-90)
        )
        sensor_8 = world.spawn_actor(cam_bp, spawn_point_8, attach_to=None)
        sensor_8.listen(lambda data: self.sensor_callback(weak_self, data, "000"))
        self.sensor_list.append(sensor_8)

        spawn_point_18 = carla.Transform(
            carla.Location(x=mylights[18].location.x, z=mylights[18].location.z + 10, y=mylights[18].location.y),
            carla.Rotation(pitch=-15, yaw=45)
        )
        sensor_18 = world.spawn_actor(cam_bp, spawn_point_18, attach_to=None)
        sensor_18.listen(lambda data: self.sensor_callback(weak_self, data, "001"))
        self.sensor_list.append(sensor_18)

        spawn_point_31 = carla.Transform(
            carla.Location(x=mylights[31].location.x, z=mylights[31].location.z + 5, y=mylights[31].location.y),
            carla.Rotation(pitch=-15, yaw=90)
        )
        sensor_31 = world.spawn_actor(cam_bp, spawn_point_31, attach_to=None)
        sensor_31.listen(lambda data: self.sensor_callback(weak_self, data, "002"))
        self.sensor_list.append(sensor_31)

        spawn_point_34 = carla.Transform(
            carla.Location(x=mylights[34].location.x, z=mylights[34].location.z + 10, y=mylights[34].location.y),
            carla.Rotation(pitch=-15, yaw=-135)
        )
        sensor_34 = world.spawn_actor(cam_bp, spawn_point_34, attach_to=None)
        sensor_34.listen(lambda data: self.sensor_callback(weak_self, data, "003"))
        self.sensor_list.append(sensor_34)

        spawn_point_35 = carla.Transform(
            carla.Location(x=mylights[35].location.x, z=mylights[35].location.z + 5, y=mylights[35].location.y),
            carla.Rotation(pitch=-15, yaw=0)
        )
        sensor_35 = world.spawn_actor(cam_bp, spawn_point_35, attach_to=None)
        sensor_35.listen(lambda data: self.sensor_callback(weak_self, data, "004"))
        self.sensor_list.append(sensor_35)

    @staticmethod
    def sensor_callback(weak_self, img, sensor_name):
        global mutex
        mutex.acquire()

        self = weak_self()
        if not self:
            return

        cameraType = RoboCompCameraRGBDSimple.TImage()
        img.convert(self._cc[sensor_name])
        cameraType.image = img.raw_data
        cameraType.cameraID = int(sensor_name)
        cameraType.width = img.width
        cameraType.height = img.height

        try:
            print('Sending image from camera ', cameraType.cameraID)
            self.camerargbdsimplepub_proxy.pushRGBD(cameraType, RoboCompCameraRGBDSimple.TDepth())
        except Exception as e:
            print(e)

        mutex.release()
