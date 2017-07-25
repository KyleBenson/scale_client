import coapthon.defines

from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor
from scale_client.core.sensed_event import SensedEvent

from scale_client.networks.util import coap_response_success, coap_code_to_name
from scale_client.util.defaults import DEFAULT_COAP_PORT

from coapthon.client.helperclient import HelperClient as CoapClient
import coapthon.messages.response
from Queue import Empty

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
                 topic=None,
                 hostname="127.0.0.1",
                 port=DEFAULT_COAP_PORT,
                 username=None,
                 password=None,
                 use_polling=False,
                 timeout=300,
                 **kwargs):
        """
        :param broker:
        :param topic: path of remote resource this 'sensor' monitors
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

        self._topic = topic
        self._client = None  # Type: coapthon.client.helperclient.HelperClient

        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self.use_polling = use_polling
        self._timeout = timeout

        self._client_running = False
        self._is_connected = False
        # Used to properly cancel_observing on_stop()
        self._last_observe_response = None
        # We only want to use the threaded version of observe ONCE due to a bug in coapthon
        self._observe_started = False

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
        resp = self._client.get(self._topic, timeout=self._timeout)

        # XXX: when client closes the last response is a NoneType
        if resp is None:
            raise IOError("client shutting down...")
        elif coap_response_success(resp):
            return resp.payload
        else:
            raise IOError("CoAP response bad: %s" % resp)

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

    def observe_topic(self):
        """Issue observe GET request for the topic of interest."""
        def __bound_observe_callback(response):
            return self.__observe_callback(response)

        if self._client_running:
            log.debug("observing CoAP resource at topic %s" % self._topic)

            # BUGFIX: see coapthon #88 : basically, observe forces us to send a callback
            # to helperclient.send_request, which starts a thread that will hang around
            # forever waiting for responses.  Instead, we enforce that we'll only start
            # a single thread for observing by doing that the first time and hacking our
            # way around the API to send a blocking request with timeout=0 for all later
            # occurrences, which will allow the old thread to pick up the response.
            # NOTE: you cannot specify multiple different callbacks because of this!

            if not self._observe_started:
                self._client.observe(self._topic, __bound_observe_callback, self._timeout)
                self._observe_started = True
            else:
                request = self._client.mk_request(coapthon.defines.Codes.GET, self._topic)
                request.observe = 0
                try:
                    response = self._client.send_request(request, timeout=0)
                    # We shouldn't ever get the response back, but in case we do let's give it back
                    # to the thread that we want to process it...
                    self._client.queue.put(response)
                except Empty:
                    pass
        else:
            log.debug("Skipping observe_topics as client isn't running... maybe we're quitting?")

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
            event = self.make_event_with_raw_data(response.payload)
            remote_origin = 'coap://%s:%d/%s' % (self._hostname, self._port, event.get_type())
            log.debug("received content update for observed resource: %s" % remote_origin)
            # XXX: tag the event as coming from a remote CoAP resource so we don't send it back there.
            event.data['remote_origin'] = remote_origin
            if self.policy_check(event):
                self.publish(event)

            self._last_observe_response = response
            return True
        else:
            # TODO: handle error codes and try to re-observe?
            # TODO: switch to polling if observe isn't supported by the server
            log.debug("unsuccessful observe request with code: %s. Retrying later..." % coap_code_to_name(response.code))
            self.timed_call(self._timeout, self.__class__.observe_topic)
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
            self.observe_topic()

    def on_stop(self):
        if self._client and self._client_running:
            if self._last_observe_response is not None:
                self._client.cancel_observing(self._last_observe_response, True)
            self._client.close()
            self._client_running = False
        super(CoapVirtualSensor, self).on_stop()
