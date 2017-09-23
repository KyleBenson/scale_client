import asyncore
import logging
import socket

log = logging.getLogger(__name__)

from scale_client.core.threaded_application import ThreadedApplication


class UdpEchoServer(ThreadedApplication, asyncore.dispatcher):
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
        # Old-style class 'super' call... THIS MUST COME FIRST!
        asyncore.dispatcher.__init__(self)
        super(UdpEchoServer, self).__init__(broker, **kwargs)

        self.port = port
        self.buffer_size = buffer_size
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind(('', port))

    def handle_read(self):
        """Receives the echo request and responds back with the same payload."""
        data, addr = self.recvfrom(self.buffer_size)
        log.debug("EchoServer read data: %s" % data)
        self.sendto(data, addr)

    def writable(self):
        return False

    def on_start(self):
        """Starts the asyncore server to listen for incoming packets."""
        super(UdpEchoServer, self).on_start()
        self.run_in_background(asyncore.loop)

    def on_stop(self):
        self.close()
        super(UdpEchoServer, self).on_stop()