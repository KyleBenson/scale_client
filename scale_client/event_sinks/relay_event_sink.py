import socket
from scale_network_manager import ScaleNetworkManager

import logging
log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink

class RelayEventSink(EventSink):
    def __init__(self, broker, relay_port):
        EventSink.__init__(self, broker)
	self.__networkManager = ScaleNetworkManager()
        self.__neighbors = self.__network_manager.get_neighbors()  
	self.__relay_port = relay_port

    def on_start(self):
	# check to see if the current node has any neighbor

	return false

    def send(self, encoded_event):

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	for neighbor in self.__neighbors:
		sock.sendto(encoded_event, (neighbor, self.__relay_port))
    		log.info("Forwarding sensed events to neighbor " + neighbor)

    def check_available(self, event):
        if not self._loopflag:
                return False
        # TODO: backpressure?
        return True
