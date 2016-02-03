from scale_client.event_sinks.event_sink import EventSink
import socket
import struct
import threading
import scale_client.event_sinks.geocron_protobuf.geocron_header_pb2 as geocron_header_pb2
import json
import logging
import base64

log = logging.getLogger(__name__)
# go ahead and set the logger to INFO here so that we always log the events in question
log.setLevel(logging.INFO)
pi_host_list = ["192.168.0.15", "192.168.0.21", "192.168.0.23", "192.168.0.25", "192.168.0.27", "192.168.0.29"]
encoded_host_list = [struct.unpack("!I", socket.inet_aton(s))[0] for s in pi_host_list]
host = "192.168.0.17" 
port = 11000 #the port the client is supposed to send to and receive information from
encoded_server = struct.unpack("!I", socket.inet_aton("192.168.0.17"))[0] #extend hops list here

class GeocronEventSink(EventSink):
    """
    init sets up listening socket and begins a daemon thread to process sensed events 
    it receives from other clients.
    CONFIGURE HOPS TESTS BY CHANGING _test_route
    """
    def __init__(self, broker):
    	EventSink.__init__(self, broker)
        self.thread = None #initialized in init for readability. Will be assigned in build_background_thread
    	self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #set up socket to open only once
        self._s.bind((host, 11000)) 
        self._test_route = [encoded_server] #configure hop route here REPLACE 
    	self._serv_addr = ("192.168.0.17", port) #reception from any host allows transmission. Set up host when configuring header?
        self.build_background_thread()

    """
    Builds always listening thread on client to receive packets from other clients
    """
    def build_background_thread(self):
        self.thread = threading.Thread(target=self.run_in_background, args=(self._s,))
        self.thread.daemon = True
        self.thread.start()

    """
    Logic to process header if client needs to send process off to another client
    """
    def process_header(self, decoded_event, header):
        next_host = socket.inet_ntoa(struct.pack("!I",header.m_ips[0])) #save ip to send to next
        del header.m_ips[0] #remove top ip from hop list
        decoded_event['header'] = base64.b64encode(header.SerializeToString())
        reencoded_event = json.dumps(decoded_event)
        sent = self._s.sendto(reencoded_event, (next_host,port))
        #send here

    """
    Decodes an event sent and determines whether event belongs to client or should be passed on
    """
    def decode_event(self, event):
        #decode the event and check
        decoded_event = json.loads(event)
        header = base64.b64decode(decoded_event['header'])
        deserialized_header = geocron_header_pb2.GeocronHeader()
        deserialized_header.ParseFromString(header)
        if(socket.inet_ntoa(struct.pack("!I",deserialized_header.m_dest)) == host): #if header says event belongs here, for now log information to console
            log.info(event)
        else:
            self.process_header(decoded_event, deserialized_header)

    """
    Background thread indefinitely listens for messages sent to it and print them to console
    """
    def run_in_background(self, s):
        while 1:
            event, addr = s.recvfrom(1024)
            self.decode_event(event) #possibly fork off another process? or just handle it?

    """
    Whenever an event is recorded, create a header to be sent
    """
    def create_geocron_header(self, flag):
        #geocron information currently hardcoded
    	header = geocron_header_pb2.GeocronHeader()
        header.m_forward = True #to forward to another client?
        header.m_nHops = 1 #update? 
        header.m_seq = 1 #what's m_seq for?
        header.m_origin = struct.unpack("!I", socket.inet_aton(host))[0]
        header.m_dest = struct.unpack("!I", socket.inet_aton("192.168.0.17"))[0]
        if flag:
            header.m_ips.extend(self._test_route)
        else:
            header.m_ips.extend([encoded_server]) #extend hops list here
        return header.SerializeToString()

    """
    Note: send is called by EventSink's send_event function (as is encode_event to encode the data)
    """
    def send(self, encoded_event):
        msg = encoded_event
        #log.info(msg)
        sent = self._s.sendto(msg, self._serv_addr)
        print "sent message to client at port 11000"

    """
    Sends a SensedEvent object out on this sink.
    """
    def send_event(self, event):
        direct_msg = self.encode_event(event, False)
        overlay_msg = self.encode_event(event, True)
        self.send(direct_msg) #send normal message.
        self.send(overlay_msg) #send overlay message.

    """
    Tags header onto json object before encoding the event
    """
    def encode_event(self, event, flag):
        #create header and add it into the SensedEvent's data attribute
        header = self.create_geocron_header(flag)
        event.data['header'] = base64.b64encode(header)
    	return json.dumps(event.to_map())