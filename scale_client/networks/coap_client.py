from coapthon.client.helperclient import HelperClient
from coapthon import defines

from scale_client.networks.util import DEFAULT_COAP_PORT, msg_fits_one_coap_packet

import logging
log = logging.getLogger(__name__)


class CoapClient(HelperClient):
    """
    This helper class performs CoAP requests in a simplified way.
    It patches the coapthon HelperClient that has a bug in which
    the send_request call creates a thread that will never go away
    even after the response is received and handled.  This results
    in several outstanding requests getting in each others' way and
    responses going to the wrong callback as well as the client not
    quitting properly since only one of the threads properly exits
    and the others are left waiting on the Queue.

    We also patch this class to allow sending NON-confirmable messages.
    """

    def __init__(self, server_hostname, server_port=DEFAULT_COAP_PORT, sock=None, src_port=None,
                 cb_ignore_read_exception=None, cb_ignore_write_exception=None,
                 confirmable_messages=True):

        # TODO: make some @properties to keep these variables in sync with self.server
        self.server_hostname = server_hostname
        self.server_port = server_port

        # convert args for multiple versions of HelperClient
        coapthon_server_arg = (self.server_hostname, self.server_port)
        # Newer version accepts callbacks too
        try:
            super(CoapClient, self).__init__(coapthon_server_arg, sock=sock, cb_ignore_read_exception=cb_ignore_read_exception,
                                             cb_ignore_write_exception=cb_ignore_write_exception)
        except TypeError:
            super(CoapClient, self).__init__(coapthon_server_arg, sock=sock)
            assert cb_ignore_read_exception is None and cb_ignore_write_exception is None, "this coapthon version doesn't support callbacks in client constructor!"

        self.confirmable_messages = confirmable_messages

        # XXX: to request a specific source port, we can do this:
        if src_port is not None:
            self.protocol._socket.bind(('', src_port))

    ##### XXX: to allow sending non-confirmable messages, we hack/patch HelperClient
    def mk_request(self, method, path):
        request = super(CoapClient, self).mk_request(method, path)
        if not self.confirmable_messages:
            request.type = defines.Types["NON"]
        return request

    def put(self, path, payload, callback=None, timeout=None, **kwargs):
        if not msg_fits_one_coap_packet(payload):
            log.error("requested payload size of %d is too large to fit in a single CoAP packet!"
                      " Sending anyway but expect errors from the receiver...")
        super(CoapClient, self).put(path, payload=payload, callback=callback, timeout=timeout, **kwargs)


# some basic integration testing to verify this works...
if __name__ == '__main__':

    from coapthon.messages.response import Response
    def cb(response):
        """

        :param response:
        :type response: Response
        :return:
        """

        print "RESPONSE:", response.payload, "from", response.source, response.location_path

    client = CoapClient('127.0.0.1', confirmable_messages=False)

    client.observe('storage/blah', cb)
    client.observe('storage/blah2', cb)
    client.observe('storage/blah3', cb)