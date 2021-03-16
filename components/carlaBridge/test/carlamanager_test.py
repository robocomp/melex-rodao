import unittest
from unittest import mock
from unittest.mock import patch, Mock

from src.carlamanager import CarlaManager
unittest.TestLoader.sortTestMethodsUsing = None
HOST = "localhost"
PORT = 2000
MAP_NAME = "CampusV4"

client = Mock()


class TestCarlaManager(unittest.TestCase):
    def setUp(self) -> None:
        carlasensors_proxy = Mock()
        carcamerargbd_proxy = Mock()
        buildingcamerargbd_proxy = Mock()
        self.patcher = patch('src.carlamanager.carla.Client')
        self.client = self.patcher.start()
        self.carla_manager = CarlaManager(carlasensors_proxy, carcamerargbd_proxy, buildingcamerargbd_proxy)
        # self.carla_manager.initialize_world(MAP_NAME)

    def step01_create_client(self):
        self.assertTrue(self.carla_manager.create_client(host="mal", port=5000))
        self.client.side_effect = RuntimeError()
        self.assertFalse(self.carla_manager.create_client(host="mal", port=5000))

    def step02_test_load_world(self):
        self.carla_manager.initialize_world('patata')
        self.client.return_value.set_timeout.assert_called_once_with(10)
        self.client.return_value.load_world.assert_called_once_with("patata")
        self.client.return_value.load_world.return_value.get_blueprint_library.assert_called()

    def step03_test_load_vehicle(self):
        bp_library = self.client.return_value.load_world.return_value.get_blueprint_library.return_value
        self.carla_manager.load_vehicle("vehicle.carro.*")
        bp_library.filter.assert_called_once_with("vehicle.carro.*")
        bp_library.filter.side_effect = [RuntimeError(), mock.DEFAULT]
        bp_library.filter.return_value = list(["potatoes"])
        self.carla_manager.load_vehicle("potato")
        bp_library.filter.assert_called_with("vehicle.*")

    def step04_test_restart(self):
        world = self.client.return_value.load_world.return_value
        bp_library = self.client.return_value.load_world.return_value.get_blueprint_library.return_value
        bp_library.filter.side_effect = [mock.DEFAULT]
        bp_library.filter.return_value = list(["potatoes"])
        self.carla_manager.restart()
        world.spawn_actor.assert_called_once()
        bp_library.filter.assert_called_with("vehicle.carro.*")

    def _steps(self):
        for name in dir(self):  # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_initialization_steps(self):
        for name, step in self._steps():
            with self.subTest(test=name):
                step()

    # def test_destroy(self):
    #     self.fail()
    #
    # def test_move_car(self):
    #     self.fail()
    #
    # def test_save_sensor_data(self):
    #     self.fail()ç

    def tearDown(self) -> None:
        self.patcher.stop()


if __name__ == '__main__':
    unittest.main()