import weakref
from threading import Lock

import RoboCompCarlaSensors
import carla


# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================

class GnssSensor(object):
    def __init__(self, parent_actor, proxy):
        self.mutex = Lock()
        self.carlasensors_proxy = proxy
        self.sensor = None
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=parent_actor)

        self.latitude = 0
        self.longitude = 0
        self.altitude = 0
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: self._GNSS_callback(weak_self, event))

    @staticmethod
    def _GNSS_callback(weak_self, sensor_data):
        self = weak_self()
        self.mutex.acquire()
        if not self:
            return

        self.latitude = sensor_data.latitude
        self.longitude = sensor_data.longitude
        self.altitude = sensor_data.altitude

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
            self.carlasensors_proxy.updateSensorGNSS(dataGNSS)
        except Exception as e:
            print(e)

        self.mutex.release()

    def get_currentData(self):
        return self.latitude, self.longitude, self.altitude
