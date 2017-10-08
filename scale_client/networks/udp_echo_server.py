import logging
log = logging.getLogger(__name__)
# CIRCUITS-SPECIFIC: we need to use the circuits library here as we encountered occasional errors when starting an asyncio server
from circuits.net.sockets import UDPServer
from circuits import handler

from scale_client.core.application import Application


class UdpEchoServer(Application, UDPServer):
    """
    A basic echo server that listens on the specified UDP port and immediately responds to the client with a packet
    containing the same payload its request came with.  This is essentially just intended for basic testing/experiments.
    """

    def __init__(self, broker, port=9999, buffer_size=2048, **kwargs):
        """
        :param broker:
        :param port: the UDP port to listen on (default=9999)
        :param buffer_size: for receiving UDP datagrams
        :param kwargs:
        """
        super(UdpEchoServer, self).__init__(broker=broker, bind=('', port), bufsize=buffer_size, **kwargs)

    # CIRCUITS-SPECIFIC: circuits fires a 'read' event whenever we receive a datagram
    @handler("read")
    def handle_read(self, address, data):
        """Receives the echo request and responds back with the same payload."""
        log.debug("UdpEchoServer read data from %s: %s" % (address, data))
        # circuits magic lets us just return the data that will be echoed back
        return data