from scale_client.event_sinks.event_sink import EventSink
import socket
import threading

import json
import logging
log = logging.getLogger(__name__)
# go ahead and set the logger to INFO here so that we always log the events in question
log.setLevel(logging.INFO)
host = "98.164.226.77"
port = 10000 #the port this particular sink belongs to
hardcoded_receiver = 11000 #the port the client is supposed to send to

class GeocronEventSink(EventSink):
    """
    init sets up listening socket and begins a daemon thread to process sensed events 
    it receives from other clients.
    """
    def __init__(self, broker):
    	EventSink.__init__(self, broker)
        self.thread = None #initialized in init for readability. Will be assigned in build_background_thread
    	self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up socket to open only once
        self._s.bind(("", hardcoded_receiver)) 
    	self._serv_addr = ("", port) #reception from any host allows transmission. Set up host when configuring header?
        self.build_background_thread()

    def build_background_thread(self):
        self.thread = threading.Thread(target=self.run_in_background, args=())
        self.thread.daemon = True
        self.thread.start()

    """
    Background thread indefinitely listens for messages sent to it and print them to console
    """
    def run_in_background(self):
        while 1:
            data, addr = self._s.recvfrom(1024)
            print data


    def create_geocron_header(self):
    	raise NotImplementedError()

    """
    Note: send is called by EventSink's send_event function (as is encode_event to encode the data)
    """
    def send(self, encoded_event):
        msg = "geocron event sunk: %s" % encoded_event
        #log.info(msg)
        sent = self._s.sendto(msg, self._serv_addr)
        print "sent message to client at port 11000"

    def encode_event(self, event):
    	return json.dumps(event.to_map())