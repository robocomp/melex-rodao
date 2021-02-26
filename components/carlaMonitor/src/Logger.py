import time
import RoboCompMelexLogger


class Logger:
    def __init__(self, proxy, sender, headers):
        self.melexlogger_proxy = proxy
        self.sender = sender

        for namespace, headers in headers.items():
            loggerns = RoboCompMelexLogger.LogNamespace()
            loggerns.sender = self.sender
            loggerns.namespace = namespace
            loggerns.headers = headers
            self.melexlogger_proxy.createNamespace(loggerns)


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