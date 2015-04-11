import socket
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
import json

log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink

class RelayEventSink(EventSink, ScaleNetworkManager):
    def __init__(self, broker, relay_port):
        EventSink.__init__(self, broker)
        
        ScaleNetworkManager.__init__(self, broker)

        self.__neighbors = self.get_neighbors()
        self.batman_interface = self.get_batman_interface()
        self.batman_ip = self.get_interface_ip_address(self.batman_interface)
        self.batman_mac = self.get_interface_mac_address(self.batman_interface)
        self.mesh_host_id = self.batman_ip + "_" + self.batman_mac

        print self.mesh_host_id
        self.display_neighbors()

        self.__relay_port = relay_port
        
    def on_start(self):
        # check to see if the current node has any neighbor
        return false
    
    def send(self, encoded_event):
        '''
        Instead of publishing sensed events to MQTT server like MqttEventSink,
        RelayEventSink checks current node's neighbors and forwards the events
        to neighbor nodes if it finds any
        '''

        relay_event = {}
        relay_event['source'] = self.mesh_host_id
        relay_event['event'] = encoded_event
        encoded_relay_event = json.dumps(relay_event)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        for index in self.__neighbors:
            neighbor_ip_address = self.neighbors[index].get_ip_address()
            if neighbor_ip_address:
                sock.sendto(encoded_relay_event, (neighbor_ip_address, self.__relay_port))
                log.info("Forwarded sensed event to neighbor at ip address: " + neighbor_ip_address)

    def check_available(self, event):
        return True
