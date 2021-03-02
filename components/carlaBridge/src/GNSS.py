from queue import Queue
from multiprocessing import SimpleQueue
import weakref
import carla
from threading import Lock
import RoboCompCarlaSensors
from Logger import Logger

# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================

class GnssSensor(object):
    def __init__(self, parent_actor, proxy):
        self.mutex = Lock()
        self.carlasensors_proxy = proxy
        self.sensor = None
        self.gnss_queue = SimpleQueue()
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: self._GNSS_callback(weak_self, event))

    @staticmethod
    def _GNSS_callback(weak_self, sensor_data):
        # print('--- GNSS callback ---')
        self = weak_self()
        self.mutex.acquire()
        if not self:
            return

        ###################
        ## PUBLISH DATA ##
        ##################
        dataGNSS = RoboCompCarlaSensors.GNSS()
        dataGNSS.frame = sensor_data.frame
        dataGNSS.timestamp = sensor_data.timestamp
        dataGNSS.latitude = sensor_data.latitude
        dataGNSS.longitude = sensor_data.longitude
        dataGNSS.altitude = sensor_data.altitude

        try:
            # print('sending gnss data')
            self.carlasensors_proxy.updateSensorGNSS(dataGNSS)
        except Exception as e:
            print(e)

        self.mutex.release()
