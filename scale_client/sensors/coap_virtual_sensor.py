from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor
from scale_client.core.sensed_event import SensedEvent

from scale_client.network.util import coap_response_success, coap_code_to_name
from scale_client.util.defaults import DEFAULT_COAP_PORT

from coapthon.client.helperclient import HelperClient as CoapClient

import logging
log = logging.getLogger(__name__)


class CoapVirtualSensor(ThreadedVirtualSensor):
    """
    This VirtualSensor reads events from a remote CoAP server and publishes them internally.
    You can configure it to use the 'observe' feature (default) or simply poll the server
    with a GET request every *interval* seconds.
    """
    
    DEFAULT_PRIORITY = 5

    def __init__(self, broker,
                 topics=None,
                 hostname="127.0.0.1",
                 port=DEFAULT_COAP_PORT,
                 username=None,
                 password=None,
                 use_polling=False,
                 timeout=300,
                 **kwargs):
        """
        :param broker:
        :param topic: list of paths of remote resources this 'sensor' monitors
        :param hostname: hostname of remote server this 'sensor' monitors
        :param port: port of remote server
        :param username:
        :param password:
        :param use_polling: periodically polls if True, uses 'observe' feature for async updates if False
        :param timeout: timeout (in seconds) for a request (also used to periodically send observe requests
        to keep the request fresh and handle the case where it was NOT_FOUND initially)
        :param kwargs:
        """
        super(CoapVirtualSensor, self).__init__(broker, **kwargs)

        self._topics = topics
        self._client = None  # Type: coapthon.client.helperclient.HelperClient

        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self.use_polling = use_polling
        self._timeout = timeout

        if self.use_polling and len(self._topics) > 1:
            log.warning("For polling CoapSensor, only one topic will be read (round-robin) each interval!")
        self._next_topic_idx = 0

        self._client_running = False
        self._is_connected = False


    def get_type(self):
        """
        A unique human-readable identifier of the type of sensor this object represents.
        """
        return "coap_virtual_sensor"

    def read_raw(self):
        """
        This method is used for polling the specified topics (remote CoAP resources).
        Hence, it will cycle through each of them in a round-robin fashion: one GET
        request per sensor read interval.
        :return: raw data
        """
        resp = self._client.get(self._topics[self._next_topic_idx], timeout=self._timeout)
        self._next_topic_idx += 1
        if self._next_topic_idx >= len(self._topics):
            self._next_topic_idx = 0
        return resp.payload

    def make_event_with_raw_data(self, raw_data, priority=None):
        """
        This implementation assumes that the raw_data is a JSON-encoded SensedEvent already.
        :param raw_data:
        :param priority:
        :return:
        """
        # TODO: use priority? or log warning if someone tries to use it?
        try:
            ev = SensedEvent.from_json(raw_data)
            return ev
        except ValueError as e:
            log.error("Failed to decode SensedEvent from: %s" % raw_data)
            raise e

    def observe_topics(self):
        """Issue observe GET request for each topic of interest."""
        def __bound_observe_callback(response):
            return self.__observe_callback(response)

        for topic in self._topics:
            self._client.observe(topic, __bound_observe_callback, self._timeout)

    def __observe_callback(self, response):
        """
        Handles the response from an observe GET request.  If the response has an error,
        we will try observing it again at a later time (self.timeout) as we the server
        to be functional and for the resource to eventually be present.
        :param response:
        :type response: coapthon.messages.response.Response
        :return:
        """

        # XXX: when client closes the last response is a NoneType
        if response is None:
            return
        elif coap_response_success(response):
            remote_origin = 'coap://%s:%d/%s' % (self._hostname, self._port, response.location_path)
            log.debug("received content update for observed resource: %s" % remote_origin)
            event = self.make_event_with_raw_data(response.payload)
            # XXX: tag the event as coming from a remote CoAP resource so we don't send it back there.
            event.data['remote_origin'] = remote_origin
            if self.policy_check(event):
                self.publish(event)
            return True
        else:
            # TODO: switch to polling if observe isn't supported by the server
            log.debug("unsuccessful observe request with code: %s. Retrying later..." % coap_code_to_name(response.code))
            self.timed_call(self._timeout, self.__class__.observe_topics, self)
            return False

    def on_start(self):
        """
        If using polling, this will start the periodic sensor loop.  If not (default), this will
        use the CoAP 'observe' feature to asynchronously receive updates to the specified topic
        and internally publish them as SensedEvents.
        """
        self.run_in_background(self.__run_client)

    def __run_client(self):
        """This runs the CoAP client in a separate thread."""

        self._client = CoapClient(server=(self._hostname, self._port))
        self._client_running = True

        if self.use_polling:
            super(CoapVirtualSensor, self).on_start()
        else:
            self.observe_topics()

    def on_stop(self):
        if self._client and self._client_running:
            self._client.close()
            self._client_running = False
