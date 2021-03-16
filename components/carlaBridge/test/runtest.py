import os
import sys
import unittest
import Ice

import context
# import your test modules
import carlamanager_test
import cameramanager_test
import gnss_test
import imu_test
import logger_test

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
# suite.addTests(loader.loadTestsFromModule(carlamanager_test))
# suite.addTests(loader.loadTestsFromModule(cameramanager_test))
# suite.addTests(loader.loadTestsFromModule(gnss_test))
# suite.addTests(loader.loadTestsFromModule(imu_test))
suite.addTests(loader.loadTestsFromModule(logger_test))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)