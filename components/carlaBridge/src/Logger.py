import time
from interfaces import RoboCompMelexLogger

from singleton import SingletonMeta


class Logger(metaclass=SingletonMeta):
    def initialize(self, proxy, sender, namespaces):
        self.melexlogger_proxy = proxy
        self.sender = sender

        for namespace, headers in namespaces.items():
            loggerns = RoboCompMelexLogger.LogNamespace()
            loggerns.sender = self.sender
            loggerns.namespace = namespace
            loggerns.headers = headers
            self.melexlogger_proxy.createNamespace(loggerns)
        super(Logger, self).__init__()
        return self

    def publish_to_logger(self, namespace, method, data):
        message = RoboCompMelexLogger.LogMessage()
        message.sender = self.sender
        message.namespace = namespace
        message.method = method
        message.file = 'specificworker.py'
        message.line = 0
        message.timeStamp = str(time.time())
        message.message = data
        message.type = 'info'
        message.fullpath = ''
        self.melexlogger_proxy.sendMessage(message)
