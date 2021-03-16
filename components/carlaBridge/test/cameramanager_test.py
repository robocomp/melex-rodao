import unittest
import weakref
from unittest.mock import patch, Mock, call

from src.CameraManager import CameraManager

unittest.TestLoader.sortTestMethodsUsing = None
HOST = "localhost"
PORT = 2000
MAP_NAME = "CampusV4"

client = Mock()


class TestCameraManager(unittest.TestCase):
    def setUp(self) -> None:
        bp_library = Mock()
        parent_actor = Mock()
        self.carcamerargbd_proxy = Mock()
        self.buildingcamerargbd_proxy = Mock()
        self.patcher = patch('src.carlamanager.carla.Client')
        self.client = self.patcher.start()
        self.camera_manager = CameraManager(bp_library, parent_actor, self.buildingcamerargbd_proxy, self.carcamerargbd_proxy)

    def step01_initialization(self):
        blueprint = self.camera_manager.blueprint_library
        cam = blueprint.find.return_value

        self.camera_manager.initialization()

        blueprint.find.assert_called()
        cam.set_attribute.assert_has_calls([
            call('image_size_x', '1280'),
            call('image_size_y', '720'),
            call('fov', '110'),
            call('image_size_x', '640'),
            call('image_size_y', '480'),
            call('fov', '50'),
            call('sensor_tick', '0.2')], any_order=True)
        self.camera_manager.world.try_spawn_actor.assert_called()

    def _steps(self):
        for name in dir(self):  # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_initialization_steps(self):
        for name, step in self._steps():
            step()

    def test_delete_sensor(self):
        self.step01_initialization()
        self.assertTrue(self.camera_manager.delete_sensor(0))
        self.assertFalse(self.camera_manager.delete_sensor(31415))

    def test_sensor_callback(self):
        weak_self = weakref.ref(self.camera_manager)
        img = Mock()
        sensor_id = 0
        self.camera_manager.initialization()
        self.camera_manager.sensor_callback(weak_self, img, sensor_id)
        img.convert.assert_called_once()
        self.carcamerargbd_proxy.pushRGBD.assert_called_once()
        self.camera_manager.sensor_callback(weak_self, img, 10)
        self.buildingcamerargbd_proxy.pushRGBD.assert_called_once()

    # def step01_create_client(self):
    #     self.assertTrue(self.carla_manager.create_client(host="mal", port=5000))
    #     self.client.side_effect = RuntimeError()
    #     self.assertFalse(self.carla_manager.create_client( host="mal", port=5000))
    #
    #
    # def step02_test_load_world(self):
    #     self.carla_manager.initialize_world("patata")
    #     self.client.return_value.set_timeout.assert_called_once_with(10)
    #     self.client.return_value.load_world.assert_called_once_with("patata")
    #     self.client.return_value.load_world.return_value.get_blueprint_library.assert_called()
    #
    # def step03_test_load_vehicle(self):
    #     bp_library = self.client.return_value.load_world.return_value.get_blueprint_library.return_value
    #     self.carla_manager.load_vehicle("vehicle.carro.*")
    #     bp_library.filter.assert_called_once_with("vehicle.carro.*")
    #     bp_library.filter.side_effect = [RuntimeError(), mock.DEFAULT]
    #     bp_library.filter.return_value = list(["potatoes"])
    #     self.carla_manager.load_vehicle("potato")
    #     bp_library.filter.assert_called_with("vehicle.*")
    #
    # def step04_test_restart(self):
    #     world = self.client.return_value.load_world.return_value
    #     bp_library = self.client.return_value.load_world.return_value.get_blueprint_library.return_value
    #     bp_library.filter.side_effect = [ mock.DEFAULT]
    #     bp_library.filter.return_value = list(["potatoes"])
    #     self.carla_manager.restart()
    #     world.spawn_actor.assert_called_once
    #     bp_library.filter.assert_called_with("vehicle.carro.*")
    #
    #
    # def _steps(self):
    #     for name in dir(self):  # dir() result is implicitly sorted
    #         if name.startswith("step"):
    #             yield name, getattr(self, name)
    #
    # def test_initialization_steps(self):
    #     for name, step in self._steps():
    #         step()

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
