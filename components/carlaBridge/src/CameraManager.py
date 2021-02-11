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
    def __init__(self, bp_library, parent_actor, camerargbdsimplepub_proxy):
        self.surface = None
        self.contFPS = 0
        self.start = time.time()
        self.sensor_width = 1280
        self.sensor_height = 720
        self.sensor_width_low = 360
        self.sensor_height_low = 280
        self._parent = parent_actor
        self.blueprint_library = bp_library
        self.camerargbdsimplepub_proxy = camerargbdsimplepub_proxy

        self.sensor_attrs = {}
        self.sensor_name_dict = {}

        self.cm_queue = SimpleQueue()

        self.world = self._parent.get_world()
        self.weak_self = weakref.ref(self)

        ###############
        ##CAR SENSORS##
        ###############
        cam_bp = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        cam_bp.set_attribute('fov', '110')

        # spawn_point_car = carla.Transform(carla.Location(x=1.6, z=1.0))
        spawn_point_car = carla.Transform(carla.Location(x=0.0, y=-0.25, z=1.0))  # Carrito de golf
        self.sensor_attrs['000'] = [spawn_point_car, parent_actor, cam_bp, cc.Raw]

        # depth_bp = self.blueprint_library.find('sensor.camera.depth')
        # cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        # cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        #
        # self.sensor_attrs['001'] = [spawn_point_car, parent_actor, depth_bp, cc.Raw]
        # self.sensor_attrs['002'] = [spawn_point_car, parent_actor, depth_bp, cc.Depth]
        # self.sensor_attrs['003'] = [spawn_point_car, parent_actor, depth_bp, cc.LogarithmicDepth]

        # ###################
        # # STREET SENSORS ##
        # ###################
        cam_bp_low = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp_low.set_attribute('image_size_x', f'{self.sensor_width_low}')
        cam_bp_low.set_attribute('image_size_y', f'{self.sensor_height_low}')
        cam_bp_low.set_attribute('fov', '110')
        cam_bp_low.set_attribute('sensor_tick', '0.2')

        lmanager = self.world.get_lightmanager()
        mylights = lmanager.get_all_lights()

        spawn_point = carla.Transform(
            carla.Location(x=mylights[8].location.x, z=mylights[8].location.z + 5, y=mylights[8].location.y),
            carla.Rotation(pitch=-15, yaw=-90))
        self.sensor_attrs['004'] = [spawn_point, None, cam_bp_low, cc.Raw]

        spawn_point = carla.Transform(
            carla.Location(x=mylights[18].location.x, z=mylights[18].location.z + 10, y=mylights[18].location.y),
            carla.Rotation(pitch=-15, yaw=45))
        self.sensor_attrs['005'] = [spawn_point, None, cam_bp_low, cc.Raw]

        spawn_point = carla.Transform(
            carla.Location(x=mylights[31].location.x, z=mylights[31].location.z + 5, y=mylights[31].location.y),
            carla.Rotation(pitch=-15, yaw=90))
        self.sensor_attrs['006'] = [spawn_point, None, cam_bp_low, cc.Raw]

        spawn_point = carla.Transform(
            carla.Location(x=mylights[34].location.x, z=mylights[34].location.z + 10, y=mylights[34].location.y),
            carla.Rotation(pitch=-15, yaw=-135))
        self.sensor_attrs['007'] = [spawn_point, None, cam_bp_low, cc.Raw]

        spawn_point = carla.Transform(
            carla.Location(x=mylights[35].location.x, z=mylights[35].location.z + 5, y=mylights[35].location.y),
            carla.Rotation(pitch=-15, yaw=0))
        self.sensor_attrs['008'] = [spawn_point, None, cam_bp_low, cc.Raw]


        # Spawn sensors
        for s in self.sensor_attrs.keys():
            self.create_sensor(s)

    def create_sensor(self, sensor_name):
        print('Creating sensor')
        spawn_point_car, parent_actor, cam_bp, _ = self.sensor_attrs[sensor_name]
        sensor = self.world.spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        sensor.listen(lambda data: self.sensor_callback(self.weak_self, data, sensor_name))
        self.sensor_name_dict[sensor_name] = sensor
        return sensor

    def delete_sensor(self, name):
        print('Deleting sensor')
        sensor = self.sensor_name_dict[name]
        sensor.stop()
        sensor.destroy()
        self.sensor_name_dict[name] = None

    @staticmethod
    def sensor_callback(weak_self, img, sensor_name):
        global mutex
        mutex.acquire()

        self = weak_self()
        if not self:
            return

        self.frame = img.frame
        self.timestamp = img.timestamp

        cameraType = RoboCompCameraRGBDSimple.TImage()
        img.convert(self.sensor_attrs[sensor_name][-1])

        cameraType.image = img.raw_data
        cameraType.cameraID = int(sensor_name)
        cameraType.width = img.width
        cameraType.height = img.height

        depthType = RoboCompCameraRGBDSimple.TDepth()

        try:
            # print('Sending image from camera ', cameraType.cameraID)
            self.camerargbdsimplepub_proxy.pushRGBD(cameraType, depthType)
        except Exception as e:
            print(e)

        mutex.release()
