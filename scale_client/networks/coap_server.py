import logging

from scale_client.core.threaded_application import ThreadedApplication

logging.basicConfig()
log = logging.getLogger(__name__)

import coapthon.defines
from coapthon.server.coap import CoAP as CoapthonServer
from coapthon.resources.resource import Resource as CoapResource

# HACK: the version of CoAPthon that we're using has a bug where it overwrites our
# logging configuration, so we just reformat it.
from scale_client.util.defaults import set_logging_config, DEFAULT_COAP_PORT
set_logging_config()

from scale_client.core.sensed_event import SensedEvent


# Users need to access the server in their other CoAP-based modules,
# so we keep a registry of them indexed by the user-assigned name.
_coap_server_instances = dict()
_DEFAULT_COAP_SERVER_NAME = '__default_scale_coap_server__'
def get_coap_server(name=_DEFAULT_COAP_SERVER_NAME):
    """
    Returns the instantiated server matching the requested name.
    :param name: the name assigned to the requested CoapServer (if unspecified it returns the default server instance)
    :raises ValueError: if the requested server wasn't found
    :return:
    """
    try:
        return _coap_server_instances[name]
    except KeyError:
        raise ValueError("Requested CoapServer %s not found! Did you remember to configure it to run?" % name)

class CoapServer(ThreadedApplication):
    """
    This special Application runs a CoAP server so that other modules may use it to store CoAP resources
    for external nodes (e.g. those running a CoapVirtualSensor) to GET/POST/PUT/etc.  It allows for
    defining custom CoapResources that can handle application-specific logic.
    """
    def __init__(self, broker,
                 server_name=_DEFAULT_COAP_SERVER_NAME,
                 hostname="0.0.0.0",
                 port=DEFAULT_COAP_PORT,
                 multicast=False,
                 **kwargs):
        """
        Simple constructor.  When on_start is called, the server will actually be run.
        :param broker: internal scale_client broker
        :param server_name: the user-assigned name for this server so as to distinguish between multiple running ones
        (if unspecified only a single server without an explicit name can be run)
        :param hostname: hostname/IP address to bind server to
        :param port: port to run server on
        :param multicast: optionally enable handling multicast requests
        :param kwargs:
        """
        super(CoapServer, self).__init__(broker=broker, **kwargs)

        self._server = None  # Type: coapthon.server.coap.CoAP

        self._hostname = hostname
        self._port = port
        self._multicast = multicast
        if multicast and hostname != coapthon.defines.ALL_COAP_NODES:
            log.warning("underlying CoAPthon library currently only supports the ALL_COAP_NODES multicast address of %s" % coapthon.defines.ALL_COAP_NODES)

        self._server_running = False
        self._is_connected = False

        # Register this server as a currently-running instance
        if server_name in _coap_server_instances:
            raise ValueError("A CoapServer with server_name %s already exists!  Aborting creation of the second one..." % server_name)
        _coap_server_instances[server_name] = self
        self._server_name = server_name

    def __run_server(self):
        log.debug("starting CoAP server at IP:port %s:%d" % (self._hostname, self._port))

        try:
            self._server = CoapthonServer(self._hostname, self._port, self._multicast)
        except TypeError:
            # coapthon 4.0.2 has a different constructor API
            self._server = CoapthonServer((self._hostname, self._port), self._multicast)
        self._server_running = True

        # Listen for remote connections GETting data, etc.
        self._server.listen()

    def on_stop(self):
        self._server.close()
        self._server_running = False
        super(CoapServer, self).on_stop()

    def on_start(self):
        self.run_in_background(self.__run_server)

    def store_event(self, event, path=None):
        """
        Stores the event as a resource at the given path in the CoAP server.
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :param path: the path at which the event should be stored (default=event.get_type())
        :return:
        """

        if path is None:
            path = event.get_type()

        assert isinstance(self._server, CoapthonServer)  # for type annotation

        # Update the resource if it exists and notify possible observers (unfortunately,
        # CoAPthon doesn't have a clean way to do exactly this since most of the lower APIs
        # assume request/response/transaction objects).
        try:
            # XXX: Ensure path is formatted properly for CoAP's internals
            if not path.startswith('/'):
                path = '/' + path
            if path.endswith('/'):
                path = path[:-1]

            res = self._server.root[path]
            assert isinstance(res, SensedEventCoapResource)
            # TODO: maybe we should go through the proper API channels (e.g. render_PUT) instead so that user-defined
            # Resources will run all the proper code paths?
            res.event = event
            self._server.notify(res)
            log.debug("updated resource at path: %s" % path)
        # Create the resource since it didn't exist.
        except KeyError:
            new_resource = SensedEventCoapResource(event)
            res = self._server.add_resource(path, new_resource)
            log.debug("%s added resource to path: %s" % ('successfully' if res else 'unsuccessfully', path))

    def is_running(self):
        return self._server_running

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
        super(SensedEventCoapResource, self).__init__(name, observable=True, allow_children=True, visible=True)
        self._event = self.payload = None
        self.event = event
        self.content_type = coapthon.defines.Content_types["application/json"]

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, ev):
        """
        Updates this resource to reflect this new event.
        :param ev:
        :return:
        """
        self._event = ev
        self.payload = self.event.to_json()

    def render_GET(self, request):
        return self

    def render_PUT(self, request):
        return self

    def render_POST(self, request):
        return self

    def render_DELETE(self, request):
        return self

    # TODO: render_POST/PUT but how to do access control?