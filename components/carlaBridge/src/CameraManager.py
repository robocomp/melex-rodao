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
        # self.sensor_width_low = 480
        # self.sensor_height_low = 360
        self.sensor_width_low = 360
        self.sensor_height_low = 280
        self._parent = parent_actor
        self.blueprint_library = bp_library
        self.camerargbdsimplepub_proxy = camerargbdsimplepub_proxy

        self.sensor_attrs = {}
        self.sensorID_dict = {}

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

        spawn_point_car = carla.Transform(carla.Location(x=0.0, y=-0.25, z=1.0))  # Carrito de golf
        self.sensor_attrs[0] = [spawn_point_car, parent_actor, cam_bp, cc.Raw]

        # depth_bp = self.blueprint_library.find('sensor.camera.depth')
        # cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        # cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        #
        # self.sensor_attrs'[1] = [spawn_point_car, parent_actor, depth_bp, cc.Raw]
        # self.sensor_attrs'[2] = [spawn_point_car, parent_actor, depth_bp, cc.Depth]
        # self.sensor_attrs'[3] = [spawn_point_car, parent_actor, depth_bp, cc.LogarithmicDepth]

        # ###################
        # # STREET SENSORS ##
        # ###################
        cam_bp_low = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp_low.set_attribute('image_size_x', f'{self.sensor_width_low}')
        cam_bp_low.set_attribute('image_size_y', f'{self.sensor_height_low}')
        cam_bp_low.set_attribute('fov', '50')
        cam_bp_low.set_attribute('sensor_tick', '0.2')

        # Civil
        spawn_point_c1 = carla.Transform(carla.Location(x=-40.70, y=57, z=9.4), carla.Rotation(yaw=-75))
        self.sensor_attrs[1] = [spawn_point_c1, None, cam_bp_low, cc.Raw]
        # Arquitectura
        spawn_point_c2 = carla.Transform(carla.Location(x=12.10, y=65.10, z=9.4), carla.Rotation(yaw=-75))
        self.sensor_attrs[2] = [spawn_point_c2, None, cam_bp_low, cc.Raw]
        # Informatica
        spawn_point_c3 = carla.Transform(carla.Location(x=67.90, y=75.70, z=9.4), carla.Rotation(yaw=-75))
        self.sensor_attrs[3] = [spawn_point_c3, None, cam_bp_low, cc.Raw]
        # Teleco
        spawn_point_c4 = carla.Transform(carla.Location(x=130.50, y=98.90, z=9.4), carla.Rotation(yaw=-75))
        self.sensor_attrs[4] = [spawn_point_c4, None, cam_bp_low, cc.Raw]
        # Magisterio(derecha)
        spawn_point_c5 = carla.Transform(carla.Location(x=286.510, y=30.50, z=8.60), carla.Rotation(yaw=90))
        self.sensor_attrs[5] = [spawn_point_c5, None, cam_bp_low, cc.Raw]
        # Magisterio(izquierda)
        spawn_point_c6 = carla.Transform(carla.Location(x=286.510, y=30.50, z=8.60), carla.Rotation(yaw=150))
        self.sensor_attrs[6] = [spawn_point_c6, None, cam_bp_low, cc.Raw]
        # VCentenario(Derecha)
        spawn_point_c7 = carla.Transform(carla.Location(x=-17, y=-29.80, z=7.60), carla.Rotation(yaw=45))
        self.sensor_attrs[7] = [spawn_point_c7, None, cam_bp_low, cc.Raw]
        # VCentenario(Centro)
        spawn_point_c8 = carla.Transform(carla.Location(x=-24.10, y=-29, z=7.60), carla.Rotation(yaw=100, pitch=-15))
        self.sensor_attrs[8] = [spawn_point_c8, None, cam_bp_low, cc.Raw]
        # VCentenario(izq)
        spawn_point_c9 = carla.Transform(carla.Location(x=-32.50, y=-33.50, z=7.60), carla.Rotation(yaw=160))
        self.sensor_attrs[9] = [spawn_point_c9, None, cam_bp_low, cc.Raw]
        # Investigación(izq)
        spawn_point_c10 = carla.Transform(carla.Location(x=-164.10, y=7.2, z=12.90), carla.Rotation(yaw=160))
        self.sensor_attrs[10] = [spawn_point_c10, None, cam_bp_low, cc.Raw]
        # Investigación(rotonda)
        spawn_point_c11 = carla.Transform(carla.Location(x=-127.90, y=-9.90, z=11.80), carla.Rotation(yaw=-135, pitch=-15))
        self.sensor_attrs[11] = [spawn_point_c11, None, cam_bp_low, cc.Raw]
         # Investigación(paso de peatones)
        spawn_point_c12 = carla.Transform(carla.Location(x=-121.10, y=-7, z=11.80), carla.Rotation(yaw=-75, pitch=-20))
        self.sensor_attrs[12] = [spawn_point_c12, None, cam_bp_low, cc.Raw]
         # Investigación(derecha)
        spawn_point_c13 = carla.Transform(carla.Location(x=-121.10, y=-7, z=11.80), carla.Rotation(yaw=-15))
        self.sensor_attrs[13] = [spawn_point_c13, None, cam_bp_low, cc.Raw]

        # Spawn sensors
        for s in self.sensor_attrs.keys():
            self.create_sensor(s)

    def create_sensor(self, sensorID):
        print('Creating sensor')
        created = False
        spawn_point_car, parent_actor, cam_bp, _ = self.sensor_attrs[sensorID]
        sensor = self.world.try_spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        if sensor is not None:
            created = True
        sensor.listen(lambda data: self.sensor_callback(self.weak_self, data, sensorID))
        self.sensorID_dict[sensorID] = sensor
        return created

    def delete_sensor(self, sensorID):
        sensor = self.sensorID_dict[sensorID]
        if sensor is None:
            return False
        sensor.stop()
        deleted = sensor.destroy()
        self.sensorID_dict[sensorID] = None
        print(f'Sensor {sensorID} deleted {deleted}')
        return True

    @staticmethod
    def sensor_callback(weak_self, img, sensorID):
        global mutex
        mutex.acquire()

        self = weak_self()
        if not self:
            return

        self.frame = img.frame
        self.timestamp = img.timestamp

        cameraType = RoboCompCameraRGBDSimple.TImage()
        img.convert(self.sensor_attrs[sensorID][-1])

        cameraType.image = img.raw_data
        cameraType.cameraID = sensorID
        cameraType.width = img.width
        cameraType.height = img.height

        depthType = RoboCompCameraRGBDSimple.TDepth()

        try:
            # print('Sending image from camera ', cameraType.cameraID)
            self.camerargbdsimplepub_proxy.pushRGBD(cameraType, depthType)
        except Exception as e:
            print(e)

        mutex.release()
