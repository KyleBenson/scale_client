import re
import subprocess
import json

from pprint import pprint
import asyncore, socket

import time
from time import sleep

from scale_client.core.threaded_application import ThreadedApplication
from scale_client.core.relayed_sensed_event import RelayedSensedEvent
from scale_client.core.sensed_event import SensedEvent
from scale_client.core.application import Application
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
log = logging.getLogger(__name__)

class AsyncoreReceiverUDP(asyncore.dispatcher, RelayedSensedEvent, Application):
    def __init__(self, broker):
        asyncore.dispatcher.__init__(self)
        Application.__init__(self, broker)
       
        self.relayedSensedEvent = RelayedSensedEvent()
        self.relayedSensedEvent.__init__()

        # Bind to port 5005 on all interfaces
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(('', 3868))

        self.relayedSensedEvents = {}
        self.relayedSensedEvents['temperature'] = {}
        self.relayedSensedEvents['temperature']['neighbors_sum'] = 0.0
        self.relayedSensedEvents['temperature']['neighbors_counter'] = 0
        self.relayedSensedEvents['temperature']['neighbors_average'] = 0.0

        #self.last_time_updated = time()
        #self.refresh_interval = 60;

        self.scale_mesh_network = ScaleNetworkManager(self, 'wlan0:avahi')

    def get_mesh_host_ip(self):
        # Initial setup for SCALE Network
        self.scale_mesh_network.scan_all_interfaces()
        batman_interface = self.scale_mesh_network.get_batman_interface()

        batman_ip = self.scale_mesh_network.get_interface_ip_address(batman_interface)

        if batman_ip:
            return batman_ip
        else:
            return None

    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        log.debug("Started listening traffic from neighbor nodes ... ")
        
    # This is called everytime there is something to read
    def handle_read(self):
        try:
            data, addr = self.recvfrom(2048)
            log.debug("GOT DATA FROM NEIGHBOR")
            log.debug("Source: " + str(addr) + " >> " + data)

            if data:
                self.relayedSensedEvent.load_data(data)

                # Stop processign when data from neighbors 
                # are invalid 
                if self.relayedSensedEvent.sensor == '':
                    return 

                mesh_host_ip = self.get_mesh_host_ip() + '(mesh)'

                # Stop processing data that were generated from 
                # the host to avoid infinte loop
                if self.relayedSensedEvent.source == mesh_host_ip:
                    return 

                if(self.relayedSensedEvent.sensor == 'temperature'):
                    self.calculate_neighbors_average_temp()

                log.debug("RELAYED EVENT")
                log.debug(self.relayedSensedEvent)
                log.debug("PUBLISHING EVENT")
                sensedEvent = self.convert_to_sensed_event(self.relayedSensedEvent)
                log.debug(sensedEvent)

                # Publish relayed events from neighbors 
                # to the application
                if sensedEvent:
                    self.publish(sensedEvent)
            return
        except:
            log.error('Failed to read and publish data from neighbors')
            return

    def calculate_neighbors_average_temp(self):
        self.relayedSensedEvents['temperature']['neighbors_sum'] += self.relayedSensedEvent.data['value']
        self.relayedSensedEvents['temperature']['neighbors_counter'] += 1

        # calculate avarage temparature of all neighbors after receiving 5 
        if(self.relayedSensedEvents['temperature']['neighbors_counter'] > 5):
            self.relayedSensedEvents['temperature']['neighbors_average'] = self.relayedSensedEvents['temperature']['neighbors_sum']/self.relayedSensedEvents['temperature']['neighbors_counter']
            self.relayedSensedEvents['temperature']['neighbors_average'] = round(self.relayedSensedEvents['temperature']['neighbors_average'], 2)
   
            # Publish avarage temparature 
            self.publish_neighbors_avarage_temp()

            # reset total temp and counter
            self.relayedSensedEvents['temperature']['neighbors_counter'] = 0
            self.relayedSensedEvents['temperature']['neighbors_sum'] = 0.0
        return True

    def publish_neighbors_avarage_temp(self):
        
        data = {}
        data['event'] = 'MeshSensor'
        data['event_type'] = 'average_temperature'
        data['value'] = self.relayedSensedEvents['temperature']['neighbors_average']
        data['detail'] = {}
        data['detail']['temp_count'] = self.relayedSensedEvents['temperature']['neighbors_counter']
        data['detail']['temp_sum'] = round(self.relayedSensedEvents['temperature']['neighbors_sum'])
            
        try:
            encoded_data = json.dumps(data)
            event = SensedEvent(data['event'], data, 5)
            self.publish(event)
            log.debug('Published neighbors avarage temperature to application. Data: ' + encoded_data)

            return True
        except:
            log.error('Invalid average temparature encoded data string')
            return False

    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        pass

    def convert_to_sensed_event(self, relayedSensedEvent):
        structured_data = {"event": relayedSensedEvent.sensor, 
                "value": relayedSensedEvent.data['value'],
                "source": relayedSensedEvent.source,
                "published": relayedSensedEvent.published} 

        event = SensedEvent(relayedSensedEvent, structured_data, relayedSensedEvent.priority, relayedSensedEvent.timestamp)
        return event

def f(nsec, broker):
    AsyncoreReceiverUDP(broker)
    asyncore.loop()

class MeshRelayedEventReceiver(ThreadedApplication): 
    def on_start(self):
        self.run_in_background(f, 3, self._broker)
