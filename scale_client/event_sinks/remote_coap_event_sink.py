import logging
logging.basicConfig()
log = logging.getLogger(__name__)

from coapthon.client.helperclient import HelperClient as CoapClient
from coapthon.defines import Codes as CoapCodes
from scale_client.networks.util import coap_response_success, coap_code_to_name
from scale_client.util.defaults import DEFAULT_COAP_PORT

from event_sink import ThreadedEventSink
from scale_client.core.sensed_event import SensedEvent


class RemoteCoapEventSink(ThreadedEventSink):
    """
    This EventSink forwards events to a remote CoAP server so that other nodes
    can GET them (possibly with 'observe' enabled) as CoAP resources.
    """
    def __init__(self, broker,
                 # TODO: verify all these
                 # TODO: document what they do, especially topic
                 topic="events/%s",
                 hostname="127.0.0.1",
                 port=DEFAULT_COAP_PORT,
                 username=None,
                 password=None,
                 timeout=60,
                 **kwargs):
        super(RemoteCoapEventSink, self).__init__(broker=broker, **kwargs)

        log.debug("connecting to CoAP server at IP:port %s:%d" % (hostname, port))

        self._topic = topic
        self._client = None

        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout

        self._client_running = False
        self._is_connected = False

    def on_stop(self):
        self._client.close()
        self._client_running = False

    def on_start(self):
        self.run_in_background(self.__run_client)

    def __run_client(self):
        """This runs the CoAP client in a separate thread."""
        self._client = CoapClient(server=(self._hostname, self._port))
        self._client_running = True

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

    def __put_event_callback(self, event, response):
        """
        This callback handles the CoAP response for a PUT message.  If the response indicates
        the resource could not be found (was not present and was not created), then we'll try
        issuing a POST request instead.

        :param event: the request that we originally issued
        :type event: scale_client.core.sensed_event.SensedEvent
        :param response:
        :type response: coapthon.messages.response.Response
        :return:
        """

        # XXX: when client closes the last response is a NoneType
        if response is None:
            return
        elif coap_response_success(response):
            log.debug("successfully added resource to remote path!")
            return True
        # Seems as though we haven't created this resource yet and the server doesn't want to
        # do it for us given just a PUT request.
        elif response.code == CoapCodes.NOT_FOUND.number:
            topic = self.get_topic(event)
            log.debug("Server rejected PUT request for uncreated object: trying POST to topic %s" % topic)
            response = self._client.post(topic, event.to_json(), timeout=self._timeout)
            if coap_response_success(response):
                log.debug("successfully created resource at %s with POST method" % topic)
                return True

        log.error("failed to add resource to remote path! Code: %s" % coap_code_to_name(response.code))
        return False

    def send_event(self, event):
        """
        Stores the event as a resource in the remote CoAP server.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """

        topic = self.get_topic(event)
        log.debug("Forwarding event as CoAP remote resource: %s:%d/%s" % (self._hostname, self._port, topic))

        def __bound_put_callback(response):
            return self.__put_event_callback(event, response)
        self._client.put(topic, event.to_json(), callback=__bound_put_callback, timeout=self._timeout)

        return True

    def check_available(self, event):
        return self._client_running