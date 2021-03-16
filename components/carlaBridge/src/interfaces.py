import os
import pathlib
import time
import traceback
import Ice
import IceStorm
from rich.console import Console, Text
console = Console()

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/AdminBridge.ice")
import RoboCompAdminBridge
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/BuildingCameraRGBD.ice")
import RoboCompBuildingCameraRGBD
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/CameraRGBDSimple.ice")
import RoboCompCameraRGBDSimple
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/CarCameraRGBD.ice")
import RoboCompCCarCameraRGBD
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/CarlaSensors.ice")
import RoboCompCarlaSensors
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/CarlaVehicleControl.ice")
import RoboCompCarlaVehicleControl
Ice.loadSlice(f"-I {FILE_PATH} --all {FILE_PATH}/MelexLogger.ice")
import RoboCompMelexLogger

class ImgType(list):
    def __init__(self, iterable=list()):
        super(ImgType, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, byte)
        super(ImgType, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, byte)
        super(ImgType, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, byte)
        super(ImgType, self).insert(index, item)

setattr(RoboCompCameraRGBDSimple, "ImgType", ImgType)
class DepthType(list):
    def __init__(self, iterable=list()):
        super(DepthType, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, byte)
        super(DepthType, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, byte)
        super(DepthType, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, byte)
        super(DepthType, self).insert(index, item)

setattr(RoboCompCameraRGBDSimple, "DepthType", DepthType)
class CarlaXYZ(list):
    def __init__(self, iterable=list()):
        super(CarlaXYZ, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, float)
        super(CarlaXYZ, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, float)
        super(CarlaXYZ, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, float)
        super(CarlaXYZ, self).insert(index, item)

setattr(RoboCompCarlaSensors, "CarlaXYZ", CarlaXYZ)
class seqstring(list):
    def __init__(self, iterable=list()):
        super(seqstring, self).__init__(iterable)

    def append(self, item):
        assert isinstance(item, str)
        super(seqstring, self).append(item)

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, str)
        super(seqstring, self).extend(iterable)

    def insert(self, index, item):
        assert isinstance(item, str)
        super(seqstring, self).insert(index, item)

setattr(RoboCompMelexLogger, "seqstring", seqstring)

import adminbridgeI
import carlavehiclecontrolI



class Publishes:
    def __init__(self, ice_connector, topic_manager):
        self.ice_connector = ice_connector
        self.mprx={}
        self.topic_manager = topic_manager

        self.buildingcamerargbd = self.create_topic("BuildingCameraRGBD", RoboCompBuildingCameraRGBD.BuildingCameraRGBDPrx)

        self.carcamerargbd = self.create_topic("CarCameraRGBD", RoboCompCCarCameraRGBD.CarCameraRGBDPrx)

        self.carlasensors = self.create_topic("CarlaSensors", RoboCompCarlaSensors.CarlaSensorsPrx)

        self.melexlogger = self.create_topic("MelexLogger", RoboCompMelexLogger.MelexLoggerPrx)


    def create_topic(self, topic_name, ice_proxy):
        # Create a proxy to publish a AprilBasedLocalization topic
        topic = False
        try:
            topic = self.topic_manager.retrieve(topic_name)
        except:
            pass
        while not topic:
            try:
                topic = self.topic_manager.retrieve(topic_name)
            except IceStorm.NoSuchTopic:
                try:
                    topic = self.topic_manager.create(topic_name)
                except:
                    print(f'Another client created the {topic_name} topic? ...')
        pub = topic.getPublisher().ice_oneway()
        proxy = ice_proxy.uncheckedCast(pub)
        self.mprx[topic_name] = proxy
        return proxy

    def get_proxies_map(self):
        return self.mprx


class Requires:
    def __init__(self, ice_connector):
        self.ice_connector = ice_connector
        self.mprx={}

    def get_proxies_map(self):
        return self.mprx

    def create_proxy(self, property_name, ice_proxy):
        # Remote object connection for
        try:
            proxy_string = self.ice_connector.getProperties().getProperty(property_name)
            try:
                base_prx = self.ice_connector.stringToProxy(proxy_string)
                proxy = ice_proxy.uncheckedCast(base_prx)
                self.mprx[property_name] = proxy
                return True, proxy
            except Ice.Exception:
                print('Cannot connect to the remote object (CameraSimple)', proxy_string)
                # traceback.print_exc()
                return False, None
        except Ice.Exception as e:
            console.print_exception(e)
            console.log(f'Cannot get {property_name} property.')
            return False, None


class Subscribes:
    def __init__(self, ice_connector, topic_manager, default_handler):
        self.ice_connector = ice_connector
        self.topic_manager = topic_manager

    def create_adapter(self, property_name, interface_handler):
        adapter = self.ice_connector.createObjectAdapter(property_name)
        handler = interface_handler
        proxy = adapter.addWithUUID(handler).ice_oneway()
        topic_name = property_name.replace('Topic','')
        subscribe_done = False
        while not subscribe_done:
            try:
                topic = self.topic_manager.retrieve(topic_name)
                subscribe_done = True
            except Ice.Exception as e:
                console.log("Error. Topic does not exist (creating)", style="blue")
                time.sleep(1)
                try:
                    topic = self.topic_manager.create(topic_name)
                    subscribe_done = True
                except:
                    console.log(f"Error. Topic {Text(topic_name, style='red')} could not be created. Exiting")
                    status = 0
        qos = {}
        topic.subscribeAndGetPublisher(qos, proxy)
        adapter.activate()
        return adapter


class Implements:
    def __init__(self, ice_connector, default_handler):
        self.ice_connector = ice_connector
        self.adminbridge = self.create_adapter("AdminBridge", adminbridgeI.AdminBridgeI(default_handler))
        self.carlavehiclecontrol = self.create_adapter("CarlaVehicleControl", carlavehiclecontrolI.CarlaVehicleControlI(default_handler))

    def create_adapter(self, property_name, interface_handler):
        adapter = self.ice_connector.createObjectAdapter(property_name)
        adapter.add(interface_handler, self.ice_connector.stringToIdentity(property_name.lower()))
        adapter.activate()


class InterfaceManager:
    def __init__(self, ice_config_file):
        # TODO: Make ice connector singleton
        self.ice_config_file = ice_config_file
        self.ice_connector = Ice.initialize(self.ice_config_file)
        self.topic_manager = self.init_topic_manager()
        self.status = 0
        self.parameters = {}
        for i in self.ice_connector.getProperties():
            self.parameters[str(i)] = str(self.ice_connector.getProperties().getProperty(i))
        self.requires = Requires(self.ice_connector)
        self.publishes = Publishes(self.ice_connector, self.topic_manager)
        self.implements = None
        self.subscribes = None



    def init_topic_manager(self):
        # Topic Manager
        proxy = self.ice_connector.getProperties().getProperty("TopicManager.Proxy")
        obj = self.ice_connector.stringToProxy(proxy)
        try:
            return IceStorm.TopicManagerPrx.checkedCast(obj)
        except Ice.ConnectionRefusedException as e:
            console.log(Text('Cannot connect to rcnode! This must be running to use pub/sub.', 'red'))
            exit(-1)

    def set_default_hanlder(self, handler):
        self.implements = Implements(self.ice_connector, handler)
        self.subscribes = Subscribes(self.ice_connector, self.topic_manager, handler)

    def get_proxies_map(self):
        result = {}
        result.update(self.requires.get_proxies_map())
        result.update(self.publishes.get_proxies_map())
        return result

    def destroy(self):
        if self.ice_connector:
            self.ice_connector.destroy()



