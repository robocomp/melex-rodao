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
    def __init__(self, bp_library, parent_actor, width, height, camerargbdsimplepub_proxy):
        self.sensor = None
        self.surface = None
        self.contFPS = 0
        self.start = time.time()
        self.img_width = width
        self.img_height = height
        self._parent = parent_actor
        self.camerargbdsimplepub_proxy = camerargbdsimplepub_proxy

        self.recording = False
        self._camera_transforms = [
            carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15)),
            carla.Transform(carla.Location(x=1.6, z=1.7))]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB']]
        self.index = None
        world = self._parent.get_world()
        self.blueprint_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(width))
                bp.set_attribute('image_size_y', str(height))
            item.append(bp)

        self.sensor_list = []
        self.cm_queue = SimpleQueue()
        world = self._parent.get_world()
        weak_self = weakref.ref(self)
        self.lidar_range = 50
        self._cc = {'DepthRaw': cc.Raw,
                    'Depth': cc.Depth,
                    'DepthLogarithmic': cc.LogarithmicDepth,
                    '001': cc.Raw,
                    '002': cc.Raw,
                    '003': cc.Raw,
                    '004': cc.Raw,
                    '005': cc.Raw,
                    '006': cc.Raw,
                    'obras publicas': cc.Raw,
                    'investigacion': cc.Raw,
                    'profesorado': cc.Raw,
                    }

        cam_bp = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', f'{self.img_width}')
        cam_bp.set_attribute('image_size_y', f'{self.img_height}')
        cam_bp.set_attribute('fov', '110')
        cam_bp.set_attribute('sensor_tick', '1.0')

        ###################
        # STREET SENSORS ##
        ###################

        # lmanager = world.get_lightmanager()
        # mylights = lmanager.get_all_lights()
        #
        # spawn_point_8 = carla.Transform(
        #     carla.Location(x=mylights[8].location.x, z=mylights[8].location.z + 5, y=mylights[8].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90)
        # )
        # sensor_8 = world.spawn_actor(cam_bp, spawn_point_8, attach_to=None)
        # sensor_8.listen(lambda data: self.sensor_callback(weak_self, data, "000"))
        # self.sensor_list.append(sensor_8)
        #
        # spawn_point_18 = carla.Transform(
        #     carla.Location(x=mylights[18].location.x, z=mylights[18].location.z + 5, y=mylights[18].location.y),
        #     carla.Rotation(pitch=-15, yaw=45)
        # )
        # sensor_18 = world.spawn_actor(cam_bp, spawn_point_18, attach_to=None)
        # sensor_18.listen(lambda data: self.sensor_callback(weak_self, data, "001"))
        # self.sensor_list.append(sensor_18)
        #
        # spawn_point_31 = carla.Transform(
        #     carla.Location(x=mylights[31].location.x, z=mylights[31].location.z + 5, y=mylights[31].location.y),
        #     carla.Rotation(pitch=-15, yaw=90)
        # )
        # sensor_31 = world.spawn_actor(cam_bp, spawn_point_31, attach_to=None)
        # sensor_31.listen(lambda data: self.sensor_callback(weak_self, data, "002"))
        # self.sensor_list.append(sensor_31)
        #
        # spawn_point_34 = carla.Transform(
        #     carla.Location(x=mylights[34].location.x, z=mylights[34].location.z + 5, y=mylights[34].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90)
        # )
        # sensor_34 = world.spawn_actor(cam_bp, spawn_point_34, attach_to=None)
        # sensor_34.listen(lambda data: self.sensor_callback(weak_self, data, "003"))
        # self.sensor_list.append(sensor_34)
        #
        # spawn_point_35 = carla.Transform(
        #     carla.Location(x=mylights[35].location.x, z=mylights[35].location.z + 5, y=mylights[35].location.y),
        #     carla.Rotation(pitch=-15, yaw=0)
        # )
        # sensor_35 = world.spawn_actor(cam_bp, spawn_point_35, attach_to=None)
        # sensor_35.listen(lambda data: self.sensor_callback(weak_self, data, "004"))
        # self.sensor_list.append(sensor_35)

        ###############
        ##CAR SENSORS##
        ###############

        spawn_point_car = carla.Transform(carla.Location(x=1.6, z=1.7))

        cam05 = world.spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        cam05.listen(lambda data: self.sensor_callback(weak_self, data, '005'))
        self.sensor_list.append(cam05)

        # spawn_point_car2 =carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15))
        spawn_point_car2 = carla.Transform(carla.Location(x=15, z=30), carla.Rotation(pitch=-90))

        cam06 = world.spawn_actor(cam_bp, spawn_point_car2, attach_to=parent_actor)
        cam06.listen(lambda data: self.sensor_callback(weak_self, data, '006'))
        self.sensor_list.append(cam06)

        # depth_bp = self.blueprint_library.find('sensor.camera.depth')
        # depth_bp.set_attribute('image_size_x', f'{self.img_width}')
        # depth_bp.set_attribute('image_size_y', f'{self.img_height}')
        #
        #
        # cam05 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        # cam05.listen(lambda data: self.sensor_callback(weak_self, data, 'DepthRaw'))
        # self.sensor_list.append(cam05)
        #
        # cam06 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        # cam06.listen(lambda data: self.sensor_callback(weak_self, data, 'Depth'))
        # self.sensor_list.append(cam06)

        # cam07 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        # cam07.listen(lambda data: self.sensor_callback(weak_self, data, 'DepthLogarithmic'))
        # self.sensor_list.append(cam07)

    def show_img(self, img, sensor_name,w,h):
        # img.convert(self._cc[str(img.cameraID)])
        # array = np.frombuffer(img.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(img, (h, w, 4))
        array = array[:, :, :3]

        cv2.imshow(sensor_name, array)
        cv2.waitKey(1)

    @staticmethod
    def sensor_callback(weak_self, img, sensor_name):
        global mutex
        mutex.acquire()

        self = weak_self()
        if not self:
            return

        # if time.time() - self.start > 1:
        #     print("FPS:", self.contFPS)
        #     self.start = time.time()
        #     self.contFPS = 0
        # self.contFPS += 1

        self.frame = img.frame
        self.timestamp = img.timestamp

        cameraType = RoboCompCameraRGBDSimple.TImage()

        # img.convert(self._cc[sensor_name])
        # array = np.frombuffer(img.raw_data, dtype=np.dtype("uint8"))
        # array_bytes = array.tobytes()
        cameraType.image = img.raw_data
        cameraType.cameraID = int(sensor_name)
        cameraType.width = img.width
        cameraType.height = img.height

        depthType = RoboCompCameraRGBDSimple.TDepth()

        try:
            self.camerargbdsimplepub_proxy.pushRGBD(cameraType, depthType)
        except Exception as e:
            print(e)

        # # To show the image locally
        # img.convert(self._cc[sensor_name])
        # array = np.frombuffer(img.raw_data, dtype=np.dtype("uint8"))
        # array = np.reshape(array, (img.height, img.width, 4))
        # array = array[:, :, :3]
        # # array = array[:, :, ::-1]
        # self.cm_queue.put((self.timestamp, self.frame, sensor_name, array))

        # self.cm_queue.put((array, sensor_name))


        mutex.release()
