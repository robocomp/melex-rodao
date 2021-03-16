import unittest
import weakref
from unittest.mock import patch, Mock, call

from src.GNSS import GnssSensor

unittest.TestLoader.sortTestMethodsUsing = None
HOST = "localhost"
PORT = 2000
MAP_NAME = "CampusV4"

client = Mock()


class TestGnssSensor(unittest.TestCase):
    def setUp(self) -> None:
        # TODO: set spec_set= for the Mocks
        parent_actor = Mock()
        self.proxy = Mock()
        self.world = parent_actor.get_world.return_value
        self.sensor = self.world.spawn_actor.return_value
        self.gnss_sensor = GnssSensor(parent_actor, self.proxy)
        self.world.get_blueprint_library().find.assert_called_with('sensor.other.gnss')
        self.world.spawn_actor.assert_called()
        self.sensor.listen.assert_called()

    def test_GNSS_callback(self):
        weak_self = weakref.ref(self.gnss_sensor)
        sensor_data = Mock()
        self.gnss_sensor._GNSS_callback(weak_self, sensor_data)
        self.proxy.updateSensorGNSS.assert_called_once()

if __name__ == '__main__':
    unittest.main()
