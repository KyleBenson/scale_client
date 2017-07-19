import logging
logging.basicConfig()
log = logging.getLogger(__name__)

from coapthon.server.coap import CoAP as CoapServer
from coapthon.resources.resource import Resource as CoapResource
from coapthon import defines

# HACK: the version of CoAPthon that we're using has a bug where it overwrites our
# logging configuration, so we just reformat it.
from scale_client.util.defaults import set_logging_config, DEFAULT_COAP_PORT
set_logging_config()

from event_sink import ThreadedEventSink
from scale_client.core.sensed_event import SensedEvent


class SensedEventCoapResource(CoapResource):
    """
    Represents a SensedEvent stored as a CoAP Resource
    """
    def __init__(self, event, name="SensedEvent"):
        """
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :param name:
        :return:
        """
        super(SensedEventCoapResource, self).__init__(name)
        self.event = event
        self.payload = self.event.to_json()
        self.content_type = defines.Content_types["application/json"]

    def render_GET(self, request):
        return self


class LocalCoapEventSink(ThreadedEventSink):
    """
    This EventSink stores events in a CoAP server so that external nodes
    (e.g. those running a CoapVirtualSensor) can GET them as CoAP resources.
    """
    def __init__(self, broker,
                 # TODO: verify all these
                 # TODO: document what they do, especially topic
                 topic="events/%s",
                 hostname="0.0.0.0",
                 port=DEFAULT_COAP_PORT,
                 username=None,
                 password=None,
                 keepalive=60,
                 multicast=False,
                 **kwargs):
        super(LocalCoapEventSink, self).__init__(broker=broker, **kwargs)

        log.debug("starting CoAP server at IP:port %s:%d" % (hostname, port))

        self._topic = topic
        self._server = None  # Type: coapthon.server.coap.CoAP

        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self._keepalive = keepalive
        self._multicast = multicast

        self._server_running = False
        self._is_connected = False

    def __run_server(self):
        try:
            self._server = CoapServer(self._hostname, self._port, self._multicast)
        except TypeError:
            # coapthon 4.0.2 has a different constructor API
            self._server = CoapServer((self._hostname, self._port), self._multicast)
        self._server_running = True

        # We first need to create the root resource for all the other events.
        event = SensedEvent('events', priority=1, data='root of events resources')
        self.send_event(event)

        # Listen for remote connections GETting data, etc.
        # TODO: set timeout?  says it's used for checking if server should stop
        # TODO: make this configurable?  an event_sink may just be a client that PUTs data in a remote server instead
        self._server.listen()

    def on_stop(self):
        self._server.close()
        self._server_running = False

    def on_start(self):
        self.run_in_background(self.__run_server)

    def get_topic(self, event):
        """
        Builds the topic for the particular event.  This will be used for
        the resource URI.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """
        # Resource paths must end with /
        return self._topic % event.get_type() + '/'

    def send_event(self, event):
        """
        Stores the event as a resource in the CoAP server.  If configured for
        sending to a remote server, sends the event as a resource to that server.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """

        topic = self.get_topic(event)
        assert isinstance(self._server, CoapServer)  # for type annotation
        new_resource = SensedEventCoapResource(event)
        res = self._server.add_resource(topic, new_resource)
        log.debug("%s added resource to path: %s" % ('successfully' if res else 'unsuccessfully', topic))

    def check_available(self, event):
        return self._server_running