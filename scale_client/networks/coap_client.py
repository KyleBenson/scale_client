from coapthon.client.helperclient import HelperClient
from coapthon import defines
from coapthon.messages.request import Request
from coapthon.messages.response import Response

from scale_client.networks.util import coap_response_success, DEFAULT_COAP_PORT, msg_fits_one_coap_packet

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

        # BUGFIX XXX: we seem to get some strange errors when the first time we send any messages we're doing multiple
        # asynchronously (possibly due to Coap._receiver_thread being started multiple times simultaneously), so we just
        # go ahead and start it now to prevent that issue.... Hopefully this doesn't cause problems!
        self.protocol._receiver_thread.start()

    ##### XXX: to allow sending non-confirmable messages, we hack/patch HelperClient
    def mk_request(self, method, path):
        request = super(CoapClient, self).mk_request(method, path)
        if not self.confirmable_messages:
            request.type = defines.Types["NON"]
        return request

    # TODO: weili-jiang seems to have fixed this issue #88; may want to try latest version to see if we can safely do away with this hack...
    # TODO: fix the send_request function so that it does the same thing to get the response from the Queue
    # perhaps just write a coapthon Queue wrapper class?  or a .get_response() function that returns the response
    # and whether the transaction is completed?

    def _thread_body(self, request, callback):
        """
        Private function. Send a request, wait for response and call the callback function.
        :param request: the request to send
        :param callback: the callback function
        :type request: Request
        """
        # XXX: sending multiple messages asynchronously at the same time can result in an exception being generated
        # when the multiple sending threads try to start the receiver thread at once. We should be able to just safely
        # ignore this exception...
        try:
            self.protocol.send_message(request)
        except RuntimeError as e:
            log.warning("ignoring RuntimeError (should be safe if it's about only starting a thread once) raised during"
                        " Coap.send_message() : %s" % e)

        # TODO: should probably have some other condition for quitting so that if a request or response was lost forever
        # this thread will eventually quit...
        while not self.protocol.stopped.isSet():
            response = self.queue.get(block=True)

            # response could be None if we're shutting down or if a retransmit failed too many times and client gave up
            # If we're shutting down, make sure the other threads get the notice
            if response is None and self.protocol.stopped.isSet():
                self.queue.put(None)
                return
            elif response is None:
                # TODO: how to handle a failed retransmit?  we don't know which callback thread to close...
                # we might be able to just pass this None around until the right thread receives it whose
                # request has timeouted and then it can return...
                assert request.timeouted, "thought this None response must be a failed retransmit, but this request hasn't timeouted!"
                print "FAILED RETRANSMIT!!!!  This hasn't been handled yet!!!  the handler threads might lock up now..."
                continue

            # To ensure that THIS thread-callback combo is the right handler for this response,
            # we use the message_layer to verify that it matches our original request
            assert isinstance(response, Response)
            # WARNING: this may not be thread-safe...
            transaction, send_ack = self.protocol._messageLayer.receive_response(response)
            assert transaction is not None, "HACK FAILURE: couldn't find a transaction for this response so what's going on???"

            # This response is ours!
            if transaction.request == request:
                callback(response)
                # exit this thread since we're done with this transaction, which can be:
                # 1) Error response.  No retransmits here or follow-up responses
                # 2) Simple request-response completed (OBSERVE will last persistently until canceled!)
                if not coap_response_success(response) or (transaction.completed and response.observe is None):
                    return
            # Not our response, so pass it along to the next
            else:
                self.queue.put(response)

    def stop(self):
        # XXX: closing a client that hasn't send any datagrams causes an error
        # due to joining an unstarted thread (receiver).  At this time, this may
        # skip over socket.close, but that probably doesn't matter
        # as it'll be reclaimed when the process exits.
        try:
            super(CoapClient, self).stop()
        except RuntimeError:
            log.debug("ignoring RuntimeError while closing CoapClient:"
                      " you probably just didn't send any datagrams...")

    def put(self, path, payload, callback=None, timeout=None):
        if not msg_fits_one_coap_packet(payload):
            log.error("requested payload size of %d is too large to fit in a single CoAP packet!"
                      " Sending anyway but expect errors from the receiver...")
        super(CoapClient, self).put(path, payload=payload, callback=callback, timeout=timeout)