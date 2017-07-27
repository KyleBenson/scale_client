from coapthon.client.helperclient import HelperClient
from coapthon.messages.request import Request
from coapthon.messages.response import Response

from scale_client.networks.util import coap_response_success

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
    """

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
        self.protocol.send_message(request)
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