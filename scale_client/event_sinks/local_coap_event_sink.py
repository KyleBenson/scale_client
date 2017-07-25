import logging

from scale_client.core.sensed_event import SensedEvent

logging.basicConfig()
log = logging.getLogger(__name__)

from event_sink import ThreadedEventSink
from scale_client.networks.coap_server import get_coap_server


class LocalCoapEventSink(ThreadedEventSink):
    """
    This EventSink stores events in a CoAP server so that external nodes
    (e.g. those running a CoapVirtualSensor) can GET them as CoAP resources.
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
        # We'll need to create a root resource before we can add any others,
        # but we need to do it only after the server has actually started.
        self._root_created = False

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
        log.debug('%s(name=%s) sending event with topic: %s' % (self.__class__.__name__, self._server_name, topic))

        # We first need to create the root resource for all the other events, but only
        # after we know the CoapServer started.  Hence we wait for the first time we
        # call this function as we know it won't happen unless the server is available.
        if not self._root_created:
            path = self._topic % ''
            root_event = SensedEvent(path, priority=1, data='root of SCALE events resources')
            try:
                self._server.store_event(root_event, path)
                self._root_created = True
            except IOError as e:
                log.error("Failed to store root resource for event sink: %s" % e)
                return False

        try:
            self._server.store_event(event, topic)
            return True
        except IOError as e:
            log.error("Error storing event in CoapServer: %s" % e)
            return False

    def check_available(self, event):
        return self._server is not None and self._server.is_running()