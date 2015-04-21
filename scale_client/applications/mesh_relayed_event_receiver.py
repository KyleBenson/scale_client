import re
import subprocess
import json
from uuid import getnode as get_mac

import mosquitto
from mosquitto import Mosquitto
from uuid import getnode as get_mac
from pprint import pprint
import asyncore, socket

import time
from time import sleep

from scale_client.core.threaded_application import ThreadedApplication
#from scale_client.network.scale_network_manager import ScaleNetworkManager
from scale_client.core.relayed_sensed_event import RelayedSensedEvent
from scale_client.core.sensed_event import SensedEvent
from scale_client.core.application import Application
from scale_client.applications.mqtt_relayer import MqttRelayer

import logging
log = logging.getLogger(__name__)

class AsyncoreReceiverUDP(asyncore.dispatcher, RelayedSensedEvent, Application, MqttRelayer):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        
        self.mqtt_topic = "iot-1/d/%012x/evt/%s/json" % (get_mac(), "%s")
        self.mqtt_hostname = "dime.smartamerica.io"
        #hostname: "m2m.eclipse.org"
        self.mqtt_hostport = 1883
        self.mqtt_username = None
        #username: "vbjsfwul"
        self.mqtt_password = None
        #password: "xottyHH5j9v2"
        self.mqtt_keepalive = 60
        MqttRelayer.__init__(self, self.mqtt_topic, self.mqtt_hostname, self.mqtt_hostport, self.mqtt_username, self.mqtt_password, self.mqtt_keepalive)
        self._try_connect()

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

    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        log.info("Started listening traffic from neighbor nodes ... ")
        
    # This is called everytime there is something to read
    def handle_read(self):
        data, addr = self.recvfrom(2048)
        #print "GOT DATA FROM NEIGHBOR"
        #print str(addr)+" >> "+data

        if data:
            self.relayedSensedEvent.load_data(data)
            # submit neighbor's event to Mqtt server 
            # if their events have not been submitted
            if self.relayedSensedEvent.published == 0:
                self.publish_relayed_sensed_event(self.relayedSensedEvent)

            if(self.relayedSensedEvent.sensor == 'temperature'):
                self.calculate_neighbors_average_temp()

            """
            Can not publish relayed sensed event back to the appication,
            more thoughts need to be spent here
            print "RELAYED EVENT"
            print self.relayedSensedEvent
            print "PUBLISHING EVENT"
            sensedEvent = self.convert_to_sensed_event(self.relayedSensedEvent)
            print sensedEvent
            self.publish(sensedEvent)
            """
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
        data['d'] = {}
        data['d']['timestamp'] = time.time()
        data['d']['event'] = 'average_temperature'
        data['d']['temp_average'] = self.relayedSensedEvents['temperature']['neighbors_average']
        data['d']['temp_count'] = self.relayedSensedEvents['temperature']['neighbors_counter']
        data['d']['temp_sum'] = self.relayedSensedEvents['temperature']['neighbors_sum']
            
        try:
            encoded_data = json.dumps(data)
            #print "Sent avarage temp:" + encoded_data

            self.send_to_mqtt(encoded_data)
            log.info('Sent neighbors avarage temperature to Mqtt. Data: ' + encoded_data)
            return True
        except:
            log.error('Invalid average temparature encoded data string')
            return False

    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        pass

    def convert_to_sensed_event(self, relayedSensedEvent):
        structured_data = {"event": relayedSensedEvent.sensor, "value": relayedSensedEvent.data['value']}
        
        event = SensedEvent(relayedSensedEvent, structured_data, relayedSensedEvent.priority, relayedSensedEvent.timestamp)
        return event
    
    def publish_relayed_sensed_event(self, relayedSensedEvent):
        if relayedSensedEvent.data:
            event = {}
            event['d'] = relayedSensedEvent.data

            try:
                encoded_event = json.dumps(event)
                if encoded_event:
                    self.send_to_mqtt(encoded_event)
                    return True
            except:
                log.error('Invalid relayed encoded event ')
                return False

def f(nsec):
    AsyncoreReceiverUDP()
    asyncore.loop()

class MeshRelayedEventReceiver(ThreadedApplication): 
    def on_start(self):
        self.run_in_background(f, 3)
