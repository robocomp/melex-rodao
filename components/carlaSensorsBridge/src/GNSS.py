from queue import Queue
from multiprocessing import SimpleQueue
import weakref
import carla

# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================

class GnssSensor(object):
    def __init__(self, parent_actor):
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
        self.sensor.listen(lambda event: GnssSensor._GNSS_callback(weak_self, event))

    @staticmethod
    def _GNSS_callback(weak_self, sensor_data):
        self = weak_self()
        if not self:
            return
        self.lat = sensor_data.latitude
        self.lon = sensor_data.longitude
        self.frame = sensor_data.frame
        self.timestamp = sensor_data.timestamp
        self.gnss_queue.put((self.timestamp, self.frame, self.lat, self.lon))

        # print('------------- GNSS -------------')
        # print('Latitud:', self.lat)
        # print('Longitud:', self.lon)
        # print('\n')

