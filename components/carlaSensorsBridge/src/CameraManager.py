
import glob
import os
import sys
from queue import Empty
import pygame
import numpy as np
from multiprocessing import SimpleQueue
import weakref
import cv2
from threading import Lock
import carla
from carla import ColorConverter as cc

mutex = Lock()


# # ==============================================================================
# # -- CameraManager -------------------------------------------------------------
# # ==============================================================================
#
#
class CameraManager(object):
    def __init__(self, bp_library, parent_actor, hud, width, height):
        self.sensor = None
        self.surface = None
        self.img_width = width
        self.img_height = height
        self._parent = parent_actor
        self.hud = hud
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
                bp.set_attribute('image_size_x', str(hud.dim[0]))
                bp.set_attribute('image_size_y', str(hud.dim[1]))
            item.append(bp)


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

        lmanager = world.get_lightmanager()
        mylights = lmanager.get_all_lights()

        # spawn_point_8 = carla.Transform(
        #     carla.Location(x=mylights[8].location.x, z=mylights[8].location.z + 5, y=mylights[8].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90)
        # )
        # sensor_8 = world.spawn_actor(cam_bp, spawn_point_8, attach_to=None)
        # sensor_8.listen(lambda data: self.sensor_callback(weak_self,data, "sensor8"))
        # self.sensor_list.append(sensor_8)
        #
        # spawn_point_18 = carla.Transform(
        #     carla.Location(x=mylights[18].location.x, z=mylights[18].location.z + 5, y=mylights[18].location.y),
        #     carla.Rotation(pitch=-15, yaw=45)
        # )
        # sensor_18 = world.spawn_actor(cam_bp, spawn_point_18, attach_to=None)
        # sensor_18.listen(lambda data: self.sensor_callback(weak_self,data, "sensor18"))
        # self.sensor_list.append(sensor_18)
        #
        # spawn_point_31 = carla.Transform(
        #     carla.Location(x=mylights[31].location.x, z=mylights[31].location.z + 5, y=mylights[31].location.y),
        #     carla.Rotation(pitch=-15, yaw=90)
        # )
        # sensor_31 = world.spawn_actor(cam_bp, spawn_point_31, attach_to=None)
        # sensor_31.listen(lambda data: self.sensor_callback(weak_self,data, "sensor31"))
        # self.sensor_list.append(sensor_31)
        #
        # spawn_point_34 = carla.Transform(
        #     carla.Location(x=mylights[34].location.x, z=mylights[34].location.z + 5, y=mylights[34].location.y),
        #     carla.Rotation(pitch=-15, yaw=-90)
        # )
        # sensor_34 = world.spawn_actor(cam_bp, spawn_point_34, attach_to=None)
        # sensor_34.listen(lambda data: self.sensor_callback(weak_self,data, "sensor34"))
        # self.sensor_list.append(sensor_34)
        #
        # spawn_point_35 = carla.Transform(
        #     carla.Location(x=mylights[35].location.x, z=mylights[35].location.z + 5, y=mylights[35].location.y),
        #     carla.Rotation(pitch=-15, yaw=0)
        # )
        # sensor_35 = world.spawn_actor(cam_bp, spawn_point_35, attach_to=None)
        # sensor_35.listen(lambda data: self.sensor_callback(weak_self,data, "sensor35"))
        # self.sensor_list.append(sensor_35)

        spawn_point_car = carla.Transform(carla.Location(x=2.5, z=0.7))
        cam04 = world.spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        cam04.listen(lambda data: self.sensor_callback(weak_self, data, 'camera RGB 04'))
        self.sensor_list.append(cam04)

        depth_bp = self.blueprint_library.find('sensor.camera.depth')
        depth_bp.set_attribute('image_size_x', f'{self.img_width}')
        depth_bp.set_attribute('image_size_y', f'{self.img_height}')


        # cam05 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        # cam05.listen(lambda data: self.sensor_callback(weak_self, data, 'DepthRaw'))
        # self.sensor_list.append(cam05)
        #
        # cam06 = world.spawn_actor(depth_bp, spawn_point_car, attach_to=parent_actor)
        # cam06.listen(lambda data: self.sensor_callback(weak_self, data, 'Depth'))
        # self.sensor_list.append(cam06)

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


    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.sensor.set_transform(self._camera_transforms[self.transform_index])

    def set_sensor(self, index, notify=True):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None \
            else self.sensors[index][0] != self.sensors[self.index][0]
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index],
                attach_to=self._parent)
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return

        image.convert(self.sensors[self.index][1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)