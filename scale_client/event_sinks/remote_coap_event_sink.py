import logging
logging.basicConfig()
log = logging.getLogger(__name__)

from coapthon.defines import Codes as CoapCodes
from scale_client.networks.util import coap_response_success, coap_code_to_name, DEFAULT_COAP_PORT
# this is basically replaceable by the coapthon HelperClient, but this version has a bugfix (see below)
from scale_client.networks.coap_client import CoapClient
from scale_client.util import uri

from event_sink import ThreadedEventSink


class RemoteCoapEventSink(ThreadedEventSink):
    """
    This EventSink forwards events to a remote CoAP server so that other nodes
    can GET them (possibly with 'observe' enabled) as CoAP resources.
    """
    def __init__(self, broker,
                 topic="/events/%s",
                 hostname="127.0.0.1",
                 port=DEFAULT_COAP_PORT,
                 src_port=None,
                 confirmable_messages=True,
                 username=None,
                 password=None,
                 timeout=60,
                 **kwargs):
        """
        :param broker:
        :param topic: used as the URI path of the remote CoAP server where the events will be sunk.  Note that you
          should include a '%s' in it to be filled with the event topic!
        :param hostname:
        :param port:
        :param src_port: optional source port number to bind our CoapClient's socket to
        :param confirmable_messages: if True (default), sends confirmable messages; otherwise they'll be best-effort
        :param username:
        :param password:
        :param timeout:
        :param kwargs:
        """
        super(RemoteCoapEventSink, self).__init__(broker=broker, **kwargs)

        log.debug("connecting to CoAP server at IP:port %s:%d" % (hostname, port))

        self._topic = topic
        self._client = None

        self._hostname = hostname
        self._port = port
        self._src_port = src_port
        self._confirmable_messages = confirmable_messages
        if username is not None or password is not None:
            log.warning("SECURITY authentication using username & password not yet supported!")
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
        self._client = CoapClient(server_hostname=self._hostname, server_port=self._port, src_port=self._src_port,
                                  confirmable_messages=self._confirmable_messages)
        self._client_running = True

    def get_topic(self, event):
        """
        Builds the topic for the particular event.  This will be used for
        the resource URI.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """
        # Resource paths must start and end with /
        topic = self._topic % event.event_type
        if not topic.startswith('/'):
            topic = '/' + topic
        if not topic.endswith('/'):
            topic += '/'
        return topic

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
            log.debug("successfully added event to remote path: %s" % event)
        # Seems as though we haven't created this resource yet and the server doesn't want to
        # do it for us given just a PUT request.
        elif response.code == CoapCodes.NOT_FOUND.number:
            topic = self.get_topic(event)
            log.debug("Server rejected PUT request for uncreated object: trying POST to topic %s" % topic)

            def __bound_post_callback(post_response):
                if response is None:
                    # must've quit while handling this....
                    return
                elif coap_response_success(post_response):
                    log.debug("successfully created resource at %s with POST method" % topic)
                    return True
                else:
                    log.error("failed to add resource %s to remote path! Code: %s" % (topic, coap_code_to_name(post_response.code)))
                    return False

            # WARNING: you cannot mix the blocking and callback-based method calls!  We could probably fix the
            # blocking one too, but we've had to extend the coapthon HelperClient to fix some threading problems
            # that don't allow it to handle more than one callback-based call in a client's lifetime.

            self._client.post(topic, self.encode_event(event), callback=__bound_post_callback, timeout=self._timeout)
        else:
            log.error("server rejected PUT request: %s" % response)

    def send_event(self, event):
        """
        Stores the event as a resource in the remote CoAP server.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :return:
        """

        topic = self.get_topic(event)
        log.debug("Forwarding event as CoAP remote resource: %s:%d%s" % (self._hostname, self._port, topic))

        # WARNING: you cannot mix the blocking and callback-based method calls!  We could probably fix the
        # blocking one too, but we've had to extend the coapthon HelperClient to fix some threading problems
        # that don't allow it to handle more than one callback-based call in a client's lifetime.
        def __bound_put_callback(response):
            return self.__put_event_callback(event, response)
        self._client.put(topic, self.encode_event(event), callback=__bound_put_callback, timeout=self._timeout)

        return True

    def encode_event(self, event):
        """
        Prepares the event for transmission to the remote CoAP server and encodes it in JSON
        :param event:
        :return:
        """
        # May need to set our local source to be a remote one, but let's restore the local source afterwards
        local_event = event.is_local
        if local_event:
            old_source = event.source
            event.source = uri.get_remote_uri(event.source)

        encoding = super(RemoteCoapEventSink, self).encode_event(event)

        if local_event:
            event.source = old_source
        return encoding


    def check_available(self, event):
        """The client must be running to sink events."""
        return self._client_running and super(RemoteCoapEventSink, self).check_available(event)