import math
import weakref
from threading import Lock

import RoboCompCarlaSensors
import carla


# ==============================================================================
# -- IMUSensor -----------------------------------------------------------------
# ==============================================================================


class IMUSensor(object):
    def __init__(self, parent_actor, proxy):
        self.mutex = Lock()

        self.carlasensors_proxy = proxy
        self.sensor = None

        self.accelerometer = (0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.compass = 0.0
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find('sensor.other.imu')
        self.sensor = world.spawn_actor(
            bp, carla.Transform(), attach_to=parent_actor)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(
            lambda sensor_data: IMUSensor._IMU_callback(weak_self, sensor_data))

    @staticmethod
    def _IMU_callback(weak_self, sensor_data):
        self = weak_self()
        self.mutex.acquire()
        if not self:
            return

        limits = (-99.9, 99.9)

        self.accelerometer = (
            max(limits[0], min(limits[1], sensor_data.accelerometer.x)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.y)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.z)))

        self.gyroscope = (
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.x))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.y))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.z))))

        self.compass = math.degrees(sensor_data.compass)
        self.frame = sensor_data.frame
        self.timestamp = sensor_data.timestamp

        ###################
        ## PUBLISH DATA ##
        ##################
        dataIMU = RoboCompCarlaSensors.IMU()
        dataIMU.frame = sensor_data.frame
        dataIMU.timestamp = sensor_data.timestamp
        dataIMU.accelerometer = self.accelerometer
        dataIMU.gyroscope = self.gyroscope
        dataIMU.compass = self.compass

        try:
            self.carlasensors_proxy.updateSensorIMU(dataIMU)
        except Exception as e:
            print(e)

        self.mutex.release()
