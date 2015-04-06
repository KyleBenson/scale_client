import re
import subprocess
import socket
import json
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
log = logging.getLogger(__name__)


class RemoteVirtualSensor(VirtualSensor):
    def __init__(self, broker, relay_port=3868, device=None):
        VirtualSensor.__init__(self, broker, device)
        self.relay_port = relay_port
        # Need to call network manager to get node
        # wireless mesh mac interface and status of each 
        # available interfaces: wifi, batman and ethernet
        self.__networkManager = ScaleNetworkManager()

    def get_type(self):
        return "remoteSensor"

    def on_start(self):
        # TODO: asynchronous callback when something is actually available on this pipe
		super(RemoteVirtualSensor, self).on_start()

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

    def replay_and_store_event(self, event):
        if not event:
            log.error("Receive an empty relay event. Moving forward")
            return false
        else:
            try:
                event_object = json.loads(event)
                if self.policy_check(event_object):
                    self.publish(event_object.data)
                    self.store(event_object)
                
            except ValueError, e:
                log.error("Invalid relay message") 
            return True
                              
    def policy_check(self, event):
        if not event:
            return False

        batman_interface = self._networkManager.get_batman_interface()
        host_id = self._networkManager.get_interface_ip_address(batman_interface)
        host_id += "-mac:" + self.self._networkManager.get_mac_address(batman_interface)

        if event.source == host_id:
            return False
        else:
            return True
    
    def store(self, event):
        '''
        Host receives data from its neighbors here. 
        We need to store the data in some kind of data 
        structure so that the application can query and 
        analyze it based on its need
        '''
        log.info("Got data from neighbor: " + event.source)
        log.info("Data: " + event.data)

        return
