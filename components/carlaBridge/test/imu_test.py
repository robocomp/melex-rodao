import unittest
import weakref
from unittest.mock import patch, Mock, call

from src.IMU import IMUSensor

unittest.TestLoader.sortTestMethodsUsing = None
HOST = "localhost"
PORT = 2000
MAP_NAME = "CampusV4"

client = Mock()


class TestImuSensor(unittest.TestCase):
    def setUp(self) -> None:
        # TODO: set spec_set for the Mocks
        parent_actor = Mock()
        self.proxy = Mock()
        self.world = parent_actor.get_world.return_value
        self.sensor = self.world.spawn_actor.return_value
        self.imu_sensor = IMUSensor(parent_actor, self.proxy)
        self.world.get_blueprint_library().find.assert_called_with('sensor.other.imu')
        self.world.spawn_actor.assert_called()
        self.sensor.listen.assert_called()

    def test_GNSS_callback(self):
        weak_self = weakref.ref(self.imu_sensor)
        sensor_data = Mock()
        sensor_data.accelerometer.x = 10
        sensor_data.accelerometer.y = 10
        sensor_data.accelerometer.z = 10
        sensor_data.gyroscope.x = 10
        sensor_data.gyroscope.y = 10
        sensor_data.gyroscope.z = 10
        sensor_data.compass = 12
        self.imu_sensor._IMU_callback(weak_self, sensor_data)
        self.proxy.updateSensorIMU.assert_called_once()

if __name__ == '__main__':
    unittest.main()
