#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2021 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

import glob
import os
import sys
from queue import Empty

import cv2
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from numpy import random
import re
import random

try:
    sys.path.append(glob.glob('/home/robocomp/carla_package/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    6

import carla
from IMU import IMUSensor
from GNSS import GnssSensor
from CameraManager import CameraManager

client = carla.Client('localhost', 2000)
client.set_timeout(50.0)
print('Loading world...')
world = client.load_world('CampusV3')
print('Done')
# world = client.get_world()

carla_map = world.get_map()
blueprint_library = world.get_blueprint_library()


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map, blueprint_library

        self.Period = 0
        self.world = world
        self.carla_map = carla_map
        self.blueprint_library = blueprint_library
        # self.sensor_width = 480
        # self.sensor_height = 360
        self.sensor_width = 1280
        self.sensor_height = 720
        self.vehicle = None
        self.collision_sensor = None
        # self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self.restart()

        # self.controller = DualControl(self.world)

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

        self.destroy()
        cv2.destroyAllWindows()

    def setParams(self, params):
        return True

    def restart(self):
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        blueprint = random.choice(self.blueprint_library.filter('vehicle.*'))
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        if self.vehicle is not None:
            spawn_point = self.vehicle.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.vehicle is None:
            spawn_points = self.carla_map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
        # Set up the sensors.
        # self.collision_sensor = CollisionSensor(self.player, self.hud)

        ### SENSORS ###
        self.gnss_sensor = GnssSensor(self.vehicle)
        self.imu_sensor = IMUSensor(self.vehicle)
        self.camera_manager = CameraManager(self.blueprint_library, self.vehicle, self.sensor_width,
                                            self.sensor_height, self.camerargbdsimplepub_proxy)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.vehicle)

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.vehicle.get_world().set_weather(preset[0])

    def render(self, display):
        self.camera_manager.render(display)

    def destroy(self):
        sensors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.imu_sensor.sensor,
            self.gnss_sensor.sensor]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.vehicle is not None:
            self.vehicle.destroy()

    def move_car(self, control):
        self.vehicle.apply_control(control)


    @QtCore.Slot()
    def compute(self):
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================
    #
    # SUBSCRIPTION to updateVehicleControl method from CarlaVehicleControl interface
    #
    def CarlaVehicleControl_updateVehicleControl(self, control):
        controller = carla.VehicleControl()
        controller.throttle = control.throttle
        controller.steer = control.steer
        controller.brake = control.brake
        controller.gear = int(control.gear)
        controller.hand_brake = control.handbrake
        controller.reverse = control.reverse

        self.move_car(controller)

# ===================================================================
# ===================================================================

######################
# From the RoboCompCameraRGBDSimplePub you can publish calling this methods:
# self.camerargbdsimplepub_proxy.pushRGBD(...)

######################
# From the RoboCompCarlaVehicleControl you can use this types:
# RoboCompCarlaVehicleControl.VehicleControl
