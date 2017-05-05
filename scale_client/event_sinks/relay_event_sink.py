import socket
import time
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
import json

log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink

import socket, asyncore

class AsyncoreClientUDP(asyncore.dispatcher):
    
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.buffer = ""
        
        # Network Connection Magic!
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind( ('', 0) ) # bind to all interfaces and a "random" free port.
        log.debug("Connecting to neighbor node...")
        
    # Once a "connection" is made do this stuff.
    def handle_connect(self):
        log.debug("Connected to neighbor node")
        
    # If a "connection" is closed do this stuff.
    def handle_close(self):
        self.close()
        
    # If a message has arrived, process it.
    def handle_read(self):
        data, addr = self.recv(2048)
        log.debug("Received data:" + data)
        
    # Actually sends the message if there was something in the buffer.
    def handle_write(self):
        if self.buffer != "":
            log.debug("Relay event: " + self.buffer)
            sent = self.sendto(self.buffer, (self.server, self.port))
            self.buffer = self.buffer[sent:]

class RelayEventSink(EventSink, ScaleNetworkManager):
    def __init__(self, broker, relay_port, scan_interval, refresh_socket_conns):
        EventSink.__init__(self, broker)
        
        ScaleNetworkManager.__init__(self, broker)

        self._neighbors = self.get_neighbors()
        self.batman_interface = self.get_batman_interface()
        self.batman_ip = self.get_interface_ip_address(self.batman_interface)
        self.batman_mac = self.get_interface_mac_address(self.batman_interface)
        self.mesh_host_id = self.batman_ip + "_" + self.batman_mac

        #print self.mesh_host_id
        self.display_neighbors()

        self.scan_interval = scan_interval;
        self.refresh_socket_conns = refresh_socket_conns;

        self._relay_port = relay_port
        self.last_time_scanned = time.time()
        self.last_time_refreshed= time.time()

        self._neighbor_connections = {}
        if self.batman_is_active():
            self.create_connection_to_neighbors()

    def create_connection_to_neighbors(self):
        for index in self._neighbors:
            neighbor_ip_address = self.neighbors[index].get_ip_address()
            if neighbor_ip_address:
                self._neighbor_connections[neighbor_ip_address] = AsyncoreClientUDP(neighbor_ip_address, self._relay_port)

    def on_start(self):
        # check to see if the current node has any neighbor
        return 

    def has_connection(self):
        '''
        Check to see if the current node has connection to the internet
        through eth0 or Wlan1 (wifi). To reduce overhead, we just do it
        randomly and assume that the connection stay the same until the 
        next check
        '''
        
        # Rescan the local network to have updated info
        if (time.time() - self.last_time_scanned) > self.scan_interval:
            self.scan_all_interfaces()
            self.update_neighbors()
            self.scan_arp_address()
            self.last_time_scanned = time.time()
            #reset timer so that we can check again

        eth0_ip = self.get_interface_ip_address('eth0')
        if eth0_ip:
            return True
        else:
            wlan1_ip = self.get_interface_ip_address('wlan1')
            if wlan1_ip:
                return True
            else:
                return False

    def send_raw(self, encoded_event):
        '''
        Instead of publishing sensed events to MQTT server like MqttEventSink,
        RelayEventSink checks current node's neighbors and forwards the events
        to neighbor nodes if it finds any
        '''

        # Skip the rest if batman 
        # is not active on the current node
        if not self.batman_is_active():
            return False

        relay_event = {}
        relay_event['source'] = self.mesh_host_id
        relay_event['sensed_event'] = json.loads(encoded_event)

        if self.has_connection():
            try:
                # Done relay events for MeshSensor if
                # if it has been published by current client
                if relay_event['sensed_event']['d']['event'] == 'MeshSensor':
                    return True
            except:
                return False

            relay_event['published'] = 1
        else:
            relay_event['published'] = 0

        # Check to see if the current node has connection 
        # to the internet through eth0 or Wlan1 interface


        encoded_relay_event = json.dumps(relay_event)
        log.info("Replaying event: " + encoded_relay_event) 
        
        if (time.time() - self.last_time_refreshed) > self.refresh_socket_conns:
            self.create_connection_to_neighbors()
            self.last_time_refreshed = time.time()

        for index in self._neighbors:
            neighbor_ip_address = self.neighbors[index].get_ip_address()
            if neighbor_ip_address:
                if self._neighbor_connections[neighbor_ip_address]:
                    self._neighbor_connections[neighbor_ip_address].buffer += encoded_relay_event
                    log.info("Forwarded sensed event to neighbor at ip address: " + neighbor_ip_address)

    def check_available(self, event):
        return True

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et == "internet_access":
            self._neta = ed

    def encode_event(self, event):
        # return event.to_json()
        return json.dumps({"d": event.to_map()})
