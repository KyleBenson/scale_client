from scale_client import networks
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor
from scale_client.core.sensed_event import SensedEvent

from scale_client.networks.util import coap_response_success, coap_code_to_name, DEFAULT_COAP_PORT
from scale_client.util import uri
# this is basically replaceable by the coapthon HelperClient, but this version has a bugfix (see below)
from scale_client.networks.coap_client import CoapClient

import logging
log = logging.getLogger(__name__)


class CoapSensor(ThreadedVirtualSensor):
    """
    This networked 'sensor' reads events from a remote CoAP server and publishes them internally.
    You can configure it to use the 'observe' feature (default) to receive and publish events
     asynchronously by specifying its 'subscriptions'.  Alternatively, you can have it
    simply poll the server with a GET request every *sample_interval* seconds by specifying
    that parameter.
    """
    
    DEFAULT_PRIORITY = 5

    def __init__(self, broker,
                 subscriptions=tuple(),
                 event_type="coap_sensor",
                 hostname="127.0.0.1",
                 port=DEFAULT_COAP_PORT,
                 src_port=None,
                 username=None,
                 password=None,
                 timeout=300,
                 **kwargs):
        """
        Many of these parameters are used to connect to the remote CoAP server.

        :param broker:
        :param topic: path of remote resource this 'sensor' monitors
        :param event_type: used as the default event type for events we publish (if none already specified in retrieved event)
        :param hostname: hostname of remote server this 'sensor' monitors
        :param port: port of remote server
        :param src_port: source port of client (default=None=automatically assigned by OS net stack)
        :param username:
        :param password:
        :param timeout: timeout (in seconds) for a request (also used to periodically send observe requests
        to keep the request fresh and handle the case where it was NOT_FOUND initially)
        :param kwargs:
        """
        super(CoapSensor, self).__init__(broker, event_type=event_type, **kwargs)

        self._remote_subscriptions = subscriptions
        self._client = None  # Type: coapthon.client.helperclient.HelperClient

        self._hostname = hostname
        self._port = port
        self._src_port = src_port
        if username is not None or password is not None:
            log.warning("SECURITY authentication using username & password not yet supported!")
        self._username = username
        self._password = password
        self.use_polling = self._sample_interval is not None
        self.__last_subscription_polled = 0  # since we go through them round-robin
        self._timeout = timeout

        self._client_running = False
        self._is_connected = False
        # Used to properly cancel_observing on_stop()
        self._last_observe_response = None
        # We only want to use the threaded version of observe ONCE due to a bug in coapthon
        self._observe_started = False

    def remote_path(self, uri_path):
        userinfo = None
        if self._username:
            userinfo = self._username
            if self._password:
                userinfo += ':' + self._password
        return uri.build_uri(scheme='coap' if not userinfo else 'coaps',
                             host=self._hostname, port=self._port if self._port != DEFAULT_COAP_PORT else None,
                             path=uri_path, userinfo=userinfo)

    def read_raw(self):
        """
        This method is used for polling the specified topics (remote CoAP resources).
        Hence, it will cycle through each of them in a round-robin fashion: one GET
        request per sensor read interval.
        :return: raw data
        """

        path = self._remote_subscriptions[self.__last_subscription_polled]
        self.__last_subscription_polled = (self.__last_subscription_polled + 1) % len(self._remote_subscriptions)

        resp = self._client.get(path, timeout=self._timeout)

        # XXX: when client closes the last response is a NoneType
        if resp is None:
            raise IOError("client shutting down...")
        elif coap_response_success(resp):
            log.warning("NO LONGER SUPPORTED: POLLING COAP SENSOR WITH RELAY_URI! Need to pass the URI path around correctly...")
            # maybe get it working inside self.make_event_with_raw_data() again???
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
        except (ValueError, TypeError) as e:
            log.error("Failed to decode SensedEvent from: %s" % raw_data)
            raise e

    def observe(self, path):
        """Issue observe GET request for the topic (remote path) of interest."""
        def __bound_observe_callback(response):
            return self.__observe_callback(response, path)

        if self._client_running:
            log.debug("observing CoAP resource at topic %s" % path)

            # WARNING: you cannot mix the blocking and callback-based method calls!  We could probably fix the
            # blocking one too, but we've had to extend the coapthon HelperClient to fix some threading problems
            # that don't allow it to handle more than one callback-based call in a client's lifetime.

            self._client.observe(path, __bound_observe_callback, self._timeout)
        else:
            log.debug("Skipping observe_topics as client isn't running... maybe we're quitting?")

    def __observe_callback(self, response, path):
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
            # TODO: figure out why we sometimes get a None payload?
            if response.payload is None:
                log.warning("EMPTY PAYLOAD for supposedly successful coap response!")
                return

            event = self.make_event_with_raw_data(response.payload)
            remote_path = self.remote_path(path)
            networks.util.process_remote_event(event, relay_uri=remote_path)

            log.debug("received content update for observed resource: %s" % remote_path)
            if self.policy_check(event):
                self.publish(event)

            self._last_observe_response = response
            return True
        else:
            # TODO: handle error codes and try to re-observe?
            # TODO: switch to polling if observe isn't supported by the server
            log.debug("unsuccessful observe request with code: %s. Retrying later..." % coap_code_to_name(response.code))
            self.timed_call(self._timeout, self.__class__.observe, repeat=False, path=path)
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

        self._client = CoapClient(server_hostname=self._hostname, server_port=self._port, src_port=self._src_port)
        self._client_running = True

        if self.use_polling:
            super(CoapSensor, self).on_start()
        else:
            for sub in self._remote_subscriptions:
                self.observe(sub)

    def on_stop(self):
        if self._client and self._client_running:
            # TODO: figure out how to cancel all observations
            if self._last_observe_response is not None:
                self._client.cancel_observing(self._last_observe_response, True)
            self._client.close()
            self._client_running = False
        super(CoapSensor, self).on_stop()
