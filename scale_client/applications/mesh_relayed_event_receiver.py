import re
import subprocess
import socket
import json

from time import sleep
from scale_client.core.threaded_application import ThreadedApplication
#from scale_client.network.scale_network_manager import ScaleNetworkManager
from scale_client.core.relayed_sensed_event import RelayedSensedEvent

import logging
log = logging.getLogger(__name__)


import asyncore, socket

class AsyncoreReceiverUDP(asyncore.dispatcher, RelayedSensedEvent):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        
        # Bind to port 5005 on all interfaces
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(('', 3868))

        self.relayedSensedEvent = RelayedSensedEvent()
        self.relayedSensedEvent.__init__()
        
    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        print "Server Started..."
        
    # This is called everytime there is something to read
    def handle_read(self):
        data, addr = self.recvfrom(2048)
        
        print "GOT DATA FROM NEIGHBOR"
        print str(addr)+" >> "+data
        if data:
            self.relayedSensedEvent.load_data(data)
            print "Relayed event type: " + self.relayedSensedEvent.get_type()

    

        ##self.publish("RelayedEvent")
        
    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        pass


def f(nsec):
    AsyncoreReceiverUDP()
    asyncore.loop()
    

class MeshRelayedEventReceiver(ThreadedApplication):

    relayed_events_pool = 0

    def on_start(self):
        self.run_in_background(f, 3)
