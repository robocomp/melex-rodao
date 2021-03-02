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
import math
import os
import sys
import traceback
from queue import Empty

import cv2
import pygame
from PySide2.QtCore import QTimer, Signal
from PySide2.QtWidgets import QApplication
from genericworker import *
from numpy import random
import re
import random
import time

carla_egg_path = os.path.join('/home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/', f'carla-*{sys.version_info.major}.{sys.version_info.minor}-linux-x86_64.egg')
try:
    print(f"Adding {glob.glob(carla_egg_path)[0]} to path")
    sys.path.append(glob.glob(carla_egg_path)[0])
except IndexError:
    print(f"Carla API not found in {carla_egg_path}")

import carla
from IMU import IMUSensor
from GNSS import GnssSensor
from CameraManager import CameraManager
from Logger import Logger


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


class SpecificWorker(GenericWorker):
    logger_signal = Signal(str, str, str)

    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map, blueprint_library

        self.Period = 0
        self.world = None
        self.blueprint_library = None
        self.vehicle = None
        self.collision_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None

        self._weather_index = 0

        self.car_moved = False
        self.last_time_car_moved = time.time()

        self.server_fps = 0
        self._server_clock = pygame.time.Clock()

        data_to_save = {
            'fps': ['Time', 'FPS'],
            'response': ['Time', 'ServerResponseTime'],
            'velocity': ['Time', 'Velocity']
        }
        self.logger = Logger(self.melexlogger_proxy, 'carlaBridge', data_to_save)
        self.logger_signal.connect(self.logger.publish_to_logger)

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
        try:
            host = params["host"]
            port = int(params["port"])
            map_name = params["map"]
            self.initialize_world(host, port, map_name)
            self.restart()

        except:
            traceback.print_exc()
            print("Error reading config params")

        return True

    def initialize_world(self, host, port, map_name):
        client = carla.Client(host, port)
        print('Client version ', client.get_client_version())
        print('Server version ', client.get_server_version())
        client.set_timeout(10.0)
        init_time = time.time()
        print('Loading world...')
        self.world = client.load_world(map_name)
        print('Done')
        print(f'Loading world took {round(time.time() - init_time)} seconds')

        # carla_map = world.get_map()
        self.blueprint_library = self.world.get_blueprint_library()

    def restart(self):
        # car_blueprints = self.blueprint_library.filter('vehicle.*')
        # for car in car_blueprints:
        #     print(car)
        try:
            blueprint = self.blueprint_library.filter('vehicle.carro.*')[0]
        except:
            blueprint = random.choice(self.world.get_blueprint_library().filter('vehicle.*'))
        # Spawn the player.
        if self.vehicle is not None:
            spawn_point = self.vehicle.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.vehicle is None:
            # spawn_points = self.carla_map.get_spawn_points()
            # spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            # self.vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
            #
            spawn_point = carla.Transform(carla.Location(x=-59.35998535, y=-4.86174774, z=2))
            self.vehicle = self.world.spawn_actor(blueprint, spawn_point)

        # Set up the sensors.
        # self.collision_sensor = CollisionSensor(self.player, self.hud)

        ### SENSORS ###
        self.gnss_sensor = GnssSensor(self.vehicle, self.carlasensors_proxy)
        self.imu_sensor = IMUSensor(self.vehicle, self.carlasensors_proxy)
        self.camera_manager = CameraManager(self.blueprint_library, self.vehicle, self.camerargbdsimplepub_proxy)

        # Connect to the callback to get server fps
        self.world.on_tick(self.on_world_tick)

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        if self.server_fps in [float("-inf"), float("inf")]:
            self.server_fps = -1
        # print('Server FPS', int(self.server_fps))
        self.logger_signal.emit('fps', 'on_world_tick', str(int(self.server_fps)))

        if self.car_moved:
            response_time = time.time() - self.last_time_car_moved
            self.car_moved = False
            self.logger_signal.emit('response', 'on_world_tick', str(response_time))

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.vehicle.get_world().set_weather(preset[0])

    def destroy(self):
        sensors = [
            self.camera_manager.sensorID_dict.values(),
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
        self.car_moved = True
        self.last_time_car_moved = time.time()

    @QtCore.Slot()
    def compute(self):
        # print(f'Camaras activas { sum(self.camera_manager.is_sensor_active.values())}')
        vel = self.vehicle.get_velocity()
        self.logger_signal.emit('velocity', 'compute', str(3.6 * math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)))

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # ===================================================================
    # ===================================================================

    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # IMPLEMENTATION of activateSensor method from AdminBridge interface
    #
    def AdminBridge_activateSensor(self, IDSensor):
        if not self.camera_manager.is_sensor_active[IDSensor]:
            ret = self.camera_manager.create_sensor(IDSensor)
            return ret

    #
    # IMPLEMENTATION of stopSensor method from AdminBridge interface
    #
    def AdminBridge_stopSensor(self, IDSensor):
        if self.camera_manager.is_sensor_active[IDSensor]:
            ret = self.camera_manager.delete_sensor(IDSensor)
            ret = self.camera_manager.delete_sensor(IDSensor)
            print('Returning ', ret)
            return True

    #
    # IMPLEMENTATION of updateVehicleControl method from CarlaVehicleControl interface
    #
    def CarlaVehicleControl_updateVehicleControl(self, control):
        controller = carla.VehicleControl()
        controller.throttle = control.throttle
        controller.steer = control.steer
        controller.brake = control.brake
        controller.gear = control.gear
        controller.hand_brake = control.handbrake
        controller.reverse = control.reverse
        controller.manual_gear_shift = control.manualgear
        self.move_car(controller)
        return True
    # ===================================================================
    # ===================================================================

    ######################
    # From the RoboCompCameraRGBDSimplePub you can publish calling this methods:
    # self.camerargbdsimplepub_proxy.pushRGBD(...)

    ######################
    # From the RoboCompCarlaSensors you can publish calling this methods:
    # self.carlasensors_proxy.updateSensorGNSS(...)
    # self.carlasensors_proxy.updateSensorIMU(...)

    ######################
    # From the RoboCompCarlaSensors you can use this types:
    # RoboCompCarlaSensors.IMU
    # RoboCompCarlaSensors.GNSS

    ######################
    # From the RoboCompMelexLogger you can publish calling this methods:
    # self.melexlogger_proxy.createNamespace(...)
    # self.melexlogger_proxy.sendMessage(...)

    ######################
    # From the RoboCompMelexLogger you can use this types:
    # RoboCompMelexLogger.LogMessage
    # RoboCompMelexLogger.LogNamespace

    ######################
    # From the RoboCompCarlaVehicleControl you can use this types:
    # RoboCompCarlaVehicleControl.VehicleControl
