import time
import weakref
from multiprocessing import SimpleQueue
from threading import Lock

import RoboCompCameraRGBDSimple
import carla
from carla import ColorConverter as cc
import yaml

mutex = Lock()


# # ==============================================================================
# # -- CameraManager -------------------------------------------------------------
# # ==============================================================================

class CameraManager(object):
    def __init__(self, bp_library, parent_actor, camerargbdsimplepub_proxy):
        self.surface = None
        self.contFPS = 0
        self.countGNSS = 0
        self.start = time.time()
        self.sensor_width = 1280
        self.sensor_height = 720
        self.sensor_width_low = 640
        self.sensor_height_low = 480
        # self.sensor_width_low = 800
        # self.sensor_height_low = 600

        self._parent = parent_actor
        self.blueprint_library = bp_library
        self.camerargbdsimplepub_proxy = camerargbdsimplepub_proxy

        self.sensor_attrs = {}
        self.sensorID_dict = {}

        self.cm_queue = SimpleQueue()

        num_cams = 13
        self.is_sensor_active = {}
        for n in range(num_cams):
            self.is_sensor_active[n] = False

        self.world = self._parent.get_world()
        self.weak_self = weakref.ref(self)

        ###############
        ##CAR SENSORS##
        ###############

        cam_bp = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        cam_bp.set_attribute('fov', '110')
        # cam_bp.set_attribute('sensor_tick', str(1 / 30))
        spawn_point_car = carla.Transform(carla.Location(x=0.0, y=-0.25, z=1.0))  # Carrito de golf
        sensor_id = 0
        self.sensor_attrs[sensor_id] = [spawn_point_car, parent_actor, cam_bp, cc.Raw]
        self.create_sensor(sensor_id)

        # depth_bp = self.blueprint_library.find('sensor.camera.depth')
        # cam_bp.set_attribute('image_size_x', f'{self.sensor_width}')
        # cam_bp.set_attribute('image_size_y', f'{self.sensor_height}')
        #
        #         self.sensor_attrs'[1] = [spawn_point_car, parent_actor, depth_bp, cc.Raw]
        #         self.sensor_attrs'[2] = [spawn_point_car, parent_actor, depth_bp, cc.Depth]
        #         self.sensor_attrs'[3] = [spawn_point_car, parent_actor, depth_bp, cc.LogarithmicDepth]

        ####################
        ## STREET SENSORS ##
        ####################
        cam_bp_low = self.blueprint_library.find('sensor.camera.rgb')
        cam_bp_low.set_attribute('image_size_x', f'{self.sensor_width_low}')
        cam_bp_low.set_attribute('image_size_y', f'{self.sensor_height_low}')
        cam_bp_low.set_attribute('fov', '50')
        cam_bp_low.set_attribute('sensor_tick', '0.2')

        parent = None
        yaml_file = open('/home/robocomp/robocomp/components/melex-rodao/etc/cameras.yml')
        pose_cameras = yaml.load(yaml_file)

        for camera_id, pose in pose_cameras.items():
            spawn_point = carla.Transform(carla.Location(x=pose['x'], y=pose['y'], z=pose['z']),
                                          carla.Rotation(yaw=pose['yaw'], pitch=pose['pitch'], roll=pose['roll']))
            self.sensor_attrs[camera_id] = [spawn_point, parent, cam_bp_low, cc.Raw]

        # # Spawn sensors
        # for s in self.sensor_attrs.keys():
        #     self.create_sensor(s)

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
        sensor = self.sensorID_dict[sensorID]
        if sensor is None:
            return False
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
            # print('Sending image from camera ', cameraType.cameraID)
            self.camerargbdsimplepub_proxy.pushRGBD(cameraType, depthType)
        except Exception as e:
            print(e)

        mutex.release()
