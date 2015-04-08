import re
import subprocess
import socket
import json
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
log = logging.getLogger(__name__)


class MeshVirtualSensor(VirtualSensor, ScaleNetworkManager):
    def __init__(self, broker, relay_port=3868, device=None):
        VirtualSensor.__init__(self, broker, device)
        ScaleNetworkManager.__init__(self, broker)
        self.relay_port = relay_port

        self.batman_interface = self.get_batman_interface()
        self.batman_ip = self.get_interface_ip_address(self.batman_interface)
        self.batman_mac = self.get_interface_mac_address(self.batman_interface)
        self.host_id = self.batman_ip + "_" + self.batman_mac
       
        print self.host_id
        self.display_neighbors()

    def get_type(self):
        return "remoteSensor"

    def on_start(self):
        # TODO: asynchronous callback when something is actually available on this pipe
        super(MeshVirtualSensor, self).on_start()

    def read(self):
        #Override VirtualSensor read() method
        super(MeshVirtualSensor, self).read()
        print "at remote virtual sensor, reading data"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        # Listen to traffic from every host on port 3868
        sock.bind(('0.0.0.0', self.relay_port))
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            print "received message:", data
            self.replay_and_store_event(data)

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
        if event.source == self.host_id:
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
