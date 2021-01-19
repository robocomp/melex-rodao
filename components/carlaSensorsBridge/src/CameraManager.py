
import glob
import os
import sys
from queue import Empty
import numpy as np
from queue import Queue
from multiprocessing import SimpleQueue
import weakref
import cv2
from threading import Thread, Lock

try:
    sys.path.append(glob.glob('/home/robocomp/carla/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

mutex = Lock()


# # ==============================================================================
# # -- CameraManager -------------------------------------------------------------
# # ==============================================================================
#
#
class CameraManager(object):
    def __init__(self, bp_library, parent_actor, width, height):
        self.sensor = None
        self.blueprint_library = bp_library
        self.img_width = width
        self.img_height = height
        self._parent = parent_actor
        self.sensor_list = []
        self.cm_queue = SimpleQueue()
        world = self._parent.get_world()
        weak_self = weakref.ref(self)
        self.lidar_range = 50
        self._cc = {'DepthRaw': cc.Raw,
                    'Depth': cc.Depth,
                    'DepthLogarithmic': cc.LogarithmicDepth,
                    'camera RGB 01': cc.Raw,
                    'camera RGB 02': cc.Raw,
                    'camera RGB 03': cc.Raw,
                    'camera RGB 04': cc.Raw,
                    'lidar': None,

                    }
        cam_bp = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', f'{self.img_width}')
        cam_bp.set_attribute('image_size_y', f'{self.img_height}')
        cam_bp.set_attribute('fov', '110')
        cam_bp.set_attribute('sensor_tick', '1.0')

        # lmanager = world.get_lightmanager()
        # mylights = lmanager.get_all_lights()
        #
        # spawn_point_16 = carla.Transform(
        #     carla.Location(x=mylights[16].location.x, z=mylights[16].location.z + 5, y=mylights[16].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90))
        # cam01 = world.spawn_actor(cam_bp, spawn_point_16, attach_to=None)
        # cam01.listen(lambda data: self.sensor_callback(weak_self, data, 'camera RGB 01'))
        # self.sensor_list.append(cam01)
        #
        # spawn_point_21 = carla.Transform(
        #     carla.Location(x=mylights[21].location.x, z=mylights[21].location.z + 5, y=mylights[21].location.y),
        #     carla.Rotation(pitch=-15, yaw=90))
        # cam02 = world.spawn_actor(cam_bp, spawn_point_21, attach_to=None)
        # cam02.listen(lambda data: self.sensor_callback(weak_self, data, 'camera RGB 02'))
        # self.sensor_list.append(cam02)
        #
        # spawn_point_5 = carla.Transform(
        #     carla.Location(x=mylights[5].location.x, z=mylights[5].location.z + 5, y=mylights[5].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90))
        # cam03 = world.spawn_actor(cam_bp, spawn_point_5, attach_to=None)
        # cam03.listen(lambda data: self.sensor_callback(weak_self, data, 'camera RGB 03'))
        # self.sensor_list.append(cam03)
        #

        spawn_point_car = carla.Transform(carla.Location(x=2.5, z=0.7))
        cam04 = world.spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        cam04.listen(lambda data: self.sensor_callback(weak_self, data, 'camera RGB 04'))
        self.sensor_list.append(cam04)

        depth_bp = self.blueprint_library.find('sensor.camera.depth')
        depth_bp.set_attribute('image_size_x', f'{self.img_width}')
        depth_bp.set_attribute('image_size_y', f'{self.img_height}')


        cam05 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        cam05.listen(lambda data: self.sensor_callback(weak_self, data, 'DepthRaw'))
        self.sensor_list.append(cam05)

        cam06 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        cam06.listen(lambda data: self.sensor_callback(weak_self, data, 'Depth'))
        self.sensor_list.append(cam06)

        cam07 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        cam07.listen(lambda data: self.sensor_callback(weak_self, data, 'DepthLogarithmic'))
        self.sensor_list.append(cam07)

    @staticmethod
    def sensor_callback(weak_self, img, sensor_name):
        global mutex
        mutex.acquire()

        self = weak_self()
        self.frame = img.frame
        self.timestamp = img.timestamp

        if not self:
            return

        img.convert(self._cc[sensor_name])
        array = np.frombuffer(img.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (img.height, img.width, 4))
        array = array[:, :, :3]
        # array = array[:, :, ::-1]
        self.cm_queue.put((self.timestamp, self.frame, sensor_name, array))

        mutex.release()

    def show_img(self, image, name):
        cv2.imshow(name, image)
        cv2.waitKey(1)

