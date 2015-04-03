import re
import subprocess
import socket
from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class RemoteVirtualSensor(VirtualSensor):
    def __init__(self, broker, relay_port=3868, device=None):
        VirtualSensor.__init__(self, broker, device)
        self.relay_port = relay_port
        print 'initial'

    def get_type(self):
        return "remoteSensor"

    def on_start(self):
        # TODO: asynchronous callback when something is actually available on this pipe
		super(RemoteVirtualSensor, self).on_start()
		print 'remote virtual sensor on start'

    def read_raw(self):
		reading = 'sensor is reading'
		print reading
		return 'remoteSensor'
    
    def read(self):
        #Override VirtualSensor read() method
        super(RemoteVirtualSensor, self).read()
        print "at remote virtual sensor, reading data"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		# Listen to traffic from every host on port 3868
        sock.bind(('0.0.0.0', self.relay_port))
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            print "received message:", data
