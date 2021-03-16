import os
import time
import weakref
from multiprocessing import SimpleQueue
from threading import Lock

import RoboCompCameraRGBDSimple
import carla
from carla import ColorConverter as cc
import yaml

mutex = Lock()

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# # ==============================================================================
# # -- CameraManager -------------------------------------------------------------
# # ==============================================================================

class CameraManager(object):
    def __init__(self, bp_library, parent_actor, buildingcamerargbd_proxy, carcamerargbd_proxy):
        self.sensor_width = 1280
        self.sensor_height = 720
        self.sensor_width_low = 640
        self.sensor_height_low = 480

        self._parent = parent_actor
        self.blueprint_library = bp_library
        self.buildingcamerargbd_proxy = buildingcamerargbd_proxy
        self.carcamerargbd_proxy = carcamerargbd_proxy

        self.sensor_attrs = {}
        self.sensorID_dict = {}
        self.world = None
        self.weak_self = None

        self.cm_queue = SimpleQueue()

        num_cams = 13
        self.is_sensor_active = {}
        for n in range(num_cams):
            self.is_sensor_active[n] = False

    def initialization(self):
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
        sensor_id = 0
        self.sensor_attrs[sensor_id] = [spawn_point_car, self._parent, cam_bp, cc.Raw]
        self.create_sensor(sensor_id)

        ####################
        ## STREET SENSORS ##
        ####################
        cam_bp_low = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp_low.set_attribute('image_size_x', f'{self.sensor_width_low}')
        cam_bp_low.set_attribute('image_size_y', f'{self.sensor_height_low}')
        cam_bp_low.set_attribute('fov', '50')
        cam_bp_low.set_attribute('sensor_tick', '0.2')

        parent = None
        cameras_yml_file = os.path.join(FILE_PATH, '..','..','..', 'etc', 'cameras.yml')
        yaml_file = open(cameras_yml_file)
        pose_cameras = yaml.load(yaml_file,  Loader=yaml.FullLoader)

        for camera_id, pose in pose_cameras.items():
            spawn_point = carla.Transform(carla.Location(x=pose['x'], y=pose['y'], z=pose['z']),
                                          carla.Rotation(yaw=pose['yaw'], pitch=pose['pitch'], roll=pose['roll']))
            self.sensor_attrs[camera_id] = [spawn_point, parent, cam_bp_low, cc.Raw]

    def create_sensor(self, sensorID):
        print('Creating sensor ',sensorID)
        created = False
        spawn_point_car, parent_actor, cam_bp, _ = self.sensor_attrs[sensorID]
        sensor = self.world.try_spawn_actor(cam_bp, spawn_point_car, attach_to=parent_actor)
        if sensor is not None:
            created = True

        sensor.listen(lambda data: self.sensor_callback(self.weak_self, data, sensorID))
        self.sensorID_dict[sensorID] = sensor
        self.is_sensor_active[sensorID] = True

        return created

    def delete_sensor(self, sensorID):
        if sensorID not in self.sensorID_dict:
            return False
        sensor = self.sensorID_dict[sensorID]
        sensor.stop()
        deleted = sensor.destroy()
        self.is_sensor_active[sensorID] = False
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
            if cameraType.cameraID == 0:
                self.carcamerargbd_proxy.pushRGBD(cameraType, depthType)
            else:
                self.buildingcamerargbd_proxy.pushRGBD(cameraType, depthType)
        except Exception as e:
            print(e)

        mutex.release()
