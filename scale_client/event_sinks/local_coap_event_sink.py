import logging

from scale_client.core.sensed_event import SensedEvent

logging.basicConfig()
log = logging.getLogger(__name__)

from event_sink import ThreadedEventSink
from scale_client.networks.coap_server import get_coap_server


class LocalCoapEventSink(ThreadedEventSink):
    """
    This EventSink stores events in a CoAP server so that external nodes
    (e.g. those running a CoapSensor) can GET them as CoAP resources.
    """
    def __init__(self, broker,
                 topic="scale/events/%s",
                 server_name=None,
                 **kwargs):
        """
        Simple constructor that looks up the server instance (make sure you configured it!) it will use.
        :param broker: internal scale_client broker
        :param topic: topic string that will be filled in (using "%s") with the event topic when it's stored
        :param server_name: the user-defined CoapServer name (optional parameter, unspecified returns default server)
        :param kwargs:
        """
        super(LocalCoapEventSink, self).__init__(broker=broker, **kwargs)

        self._topic = topic
        self._server = None
        self._server_name = server_name

    def on_start(self):
        """
        Once we've started, the CoapServer instance should be available so this is where we look it up.
        """
        if self._server_name is None:
            self._server = get_coap_server()
        else:
            self._server = get_coap_server(self._server_name)

    def get_topic(self, event):
        """
        Builds the topic for the particular event.  This will be used for
        the resource URI.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """
        # Resource paths must end with /
        return self._topic % event.event_type + '/'

    def send_event(self, event):
        """
        Stores the event as a resource in the CoAP server.  If configured for
        sending to a remote server, sends the event as a resource to that server.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """

        topic = self.get_topic(event)
        log.debug('%s(name=%s) sending event with topic: %s' % (self.__class__.__name__, self._server_name, topic))

        try:
            self._server.store_event(event, topic)
            return True
        except IOError as e:
            log.error("Error storing event in CoapServer: %s" % e)
            return False

    def check_available(self, event):
        return self._server is not None and self._server.is_running()