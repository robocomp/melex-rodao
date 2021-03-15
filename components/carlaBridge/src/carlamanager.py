import glob
import os
import random
import sys
import time

import pygame
from PySide2.QtCore import Signal, QObject
from rich.console import Console

from Logger import Logger

console = Console()
CARLA_EGG_PATH = '/home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/'
CARLA_EGG_FILE = os.path.join(CARLA_EGG_PATH,
                              f'carla-*{sys.version_info.major}.{sys.version_info.minor}-linux-x86_64.egg')
FILE_PATH = os.path.dirname(os.path.realpath(__file__))

try:
    print(f"Adding {glob.glob(CARLA_EGG_FILE)[0]} to path")
    sys.path.append(glob.glob(CARLA_EGG_FILE)[0])
except IndexError:
    console.log(f"Carla API not found in {CARLA_EGG_FILE}", style="bold red", log_locals=True)
    console.log(f"Expected \t\t{CARLA_EGG_FILE}")
    try:
        CARLA_EGG_FILE = os.path.join(FILE_PATH, '..', '..','..','files',
                                      f'carla-*{sys.version_info.major}.{sys.version_info.minor}-linux-x86_64.egg')
        print(f"Adding {glob.glob(CARLA_EGG_FILE)[0]} to path")
        sys.path.append(glob.glob(CARLA_EGG_FILE)[0])
    except IndexError:
        console.log(f"Carla API not found in {CARLA_EGG_FILE}", style="bold red", log_locals=True)
        console.log(f"Expected \t\t{CARLA_EGG_FILE}")
    for possible_file in os.listdir(CARLA_EGG_PATH):
        console.log(f"Found \t\t\t{CARLA_EGG_PATH}{possible_file}")
    exit(-1)
else:
    print(f"Importing {CARLA_EGG_FILE}")
    import carla


# from .CameraManager import CameraManager
from CameraManager import CameraManager
from GNSS import GnssSensor
from IMU import IMUSensor


class CarlaManager(QObject):
    logger_signal = Signal(str, str, str)
    def __init__(self, carlasensors_proxy, carcamerargbd_proxy, buildingcamerargbd_proxy):
        super(CarlaManager, self).__init__()
        self._server_clock = pygame.time.Clock()
        self.blueprint_library = None
        self.camera_manager = None
        self.car_moved = False

        self.client = None
        self.collision_sensor = None
        self.gnss_sensor = None
        self.imu_sensor = None
        self.last_time_car_moved = time.time()
        self.logger = Logger()
        self.map_name = None
        self.host = None
        self.port = None
        self.sensorID_dict = {}
        self.sensor_attrs = {}
        self._vehicle = None
        self.vehicle_moved = False
        self.world = None

        self.buildingcamerargbd_proxy = buildingcamerargbd_proxy
        self.buildingcamerargbd_proxy = buildingcamerargbd_proxy
        self.carcamerargbd_proxy = carcamerargbd_proxy
        self.carcamerargbd_proxy = carcamerargbd_proxy
        self.carlasensors_proxy = carlasensors_proxy

    @property
    def vehicle(self):
        if self._vehicle is None:
            console.log("No vehicle have been loaded yet. Use load_vehicle")
        else:
            return self._vehicle

    def create_client(self, host=None, port=None):
        if port is None and host is None:
            if self.host is None and self.port is None:
                console.log("Can't create Carla client without host and port")
        else:
            self.host = host
            self.port = port
        if self.client is None:
            try:
                self.client = carla.Client(self.host, self.port)
                return True
            except RuntimeError:
                console.print_exception()
        else:
            console.log(f"Carla client for {self.port} and {self.host} already exists")
        return False

    def initialize_world(self, map_name):
        if self.client:
            self.print_versions()
            self.client.set_timeout(10.0)
            init_time = time.time()
            print('Loading world...')
            self.world = self.client.load_world(map_name)
            print('Done')
            print(f'Loading world took {round(time.time() - init_time)} seconds')
            self.blueprint_library = self.world.get_blueprint_library()
            pass
        else:
            console.log("No carla client created. Call create_client first.", style="red")

    def print_versions(self):
        print('Client version ', self.client.get_client_version())
        print('Server version ', self.client.get_server_version())

    def load_vehicle(self, vehicle_name):
        try:
            blueprint = self.blueprint_library.filter(vehicle_name)[0]
        except:
            blueprint = random.choice(self.world.get_blueprint_library().filter('vehicle.*'))
        return blueprint

    def restart(self):
        vehicle_blueprint = self.load_vehicle('vehicle.carro.*')
        # Spawn the player.
        if self._vehicle is not None:
            spawn_point = self._vehicle.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self._vehicle = self.world.try_spawn_actor(vehicle_blueprint, spawn_point)
        while self._vehicle is None:
            try:
                spawn_point = carla.Transform(carla.Location(x=-59.35998535, y=-4.86174774, z=2))
                self._vehicle = self.world.spawn_actor(vehicle_blueprint, spawn_point)
            except:
                spawn_points = self.carla_map.get_spawn_points()
                spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
                self._vehicle = self.world.try_spawn_actor(vehicle_blueprint, spawn_point)

        ### SENSORS ###
        self.gnss_sensor = GnssSensor(self._vehicle, self.carlasensors_proxy)
        self.imu_sensor = IMUSensor(self._vehicle, self.carlasensors_proxy)
        self.camera_manager = CameraManager(self.blueprint_library, self._vehicle, self.buildingcamerargbd_proxy,
                                            self.carcamerargbd_proxy)

        # Connect to the callback to get server fps
        self.world.on_tick(self.on_world_tick)

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        if self.server_fps in [float("-inf"), float("inf")]:
            self.server_fps = -1
        print('Server FPS', int(self.server_fps))
        self.logger_signal.emit('fps', 'on_world_tick', str(int(self.server_fps)))

        if self.vehicle_moved:
            response_time = time.time() - self.last_time_car_moved
            self.vehicle_moved = False
            self.logger_signal.emit('response', 'on_world_tick', str(response_time))

    def destroy(self):
        sensors = [
            self.collision_sensor,
            self.imu_sensor,
            self.gnss_sensor]
        if self.camera_manager is not None:
            sensors.append( self.camera_manager.sensorID_dict.values())
        for sensor in sensors:
            if sensor is not None:
                sensor.sensor.stop()
                sensor.sensor.destroy()
        if self._vehicle is not None:
            self._vehicle.destroy()

    def move_car(self, control):
        self._vehicle.apply_control(control)
        self.vehicle_moved = True
        self.last_time_car_moved = time.time()

    def save_sensors_data(self):
        latitude, longitude, altitude = self.gnss_sensor.get_currentData()
        data = ';'.join(map(str, [latitude, longitude, altitude]))
        self.logger_signal.emit('gnss', 'CarlaSensors_updateSensorGNSS', data)

if __name__ == '__main__':
    carla_manager = CarlaManager()
    carla_manager.create_client(host="localhost", port=2000)
    carla_manager.initialize_world("CampusV4")