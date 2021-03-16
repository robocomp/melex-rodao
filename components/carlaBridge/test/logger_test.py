import unittest
from unittest.mock import patch, Mock, call

from Logger import Logger


class TestLogger(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = Logger()
        self.proxy = Mock()
        self.sender = "myself"
        headers = {
            'fps': ['Time', 'FPS'],
            'response': ['Time', 'ServerResponseTime'],
            'velocity': ['Time', 'Velocity'],
            'gnss': ['Time', 'Latitude', 'Longitude', 'Altitude'],
            'imu': ['Time', 'AccelerometerX', 'AccelerometerY', 'AccelerometerZ',
                    'GyroscopeX', 'GyroscopeY', 'GyroscopeZ', 'Compass']
        }
        self.logger.initialize(self.proxy, self.sender, headers)
        # TODO: check the parameter passed to createNamespace
        self.assertEqual(len(headers), len(self.proxy.createNamespace.mock_calls))

    def test_singleton(self):
        a = Logger()
        b = Logger()
        self.assertEqual(a, b)


    def test_publish_to_logger(self):
        namespace = "elmio"
        method = "the_method"
        data = "The data"
        self.logger.publish_to_logger(namespace, method, data)
        self.proxy.sendMessage.assert_called_once()
        self.assertEqual(self.proxy.sendMessage.call_args.args[0].namespace, namespace)
        self.assertEqual(self.proxy.sendMessage.call_args.args[0].method, method)
        self.assertEqual(self.proxy.sendMessage.call_args.args[0].message, data)
        self.assertEqual(self.proxy.sendMessage.call_args.args[0].sender, self.sender)



if __name__ == '__main__':
    unittest.main()
