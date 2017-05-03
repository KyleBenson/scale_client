"""
Various network-related utility functions to be used by apps.
"""

import time
import socket


def wait_for_internet(sleep_time=10, host="8.8.8.8", port=53, timeout=3):
    """
    Returns when Internet access (to requested URL) is established.
    :param sleep_time: seconds to sleep in between unsuccessful probe attempts
    """
    while not ping_internet(host=host, port=port, timeout=timeout):
        time.sleep(sleep_time)


def ping_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Determines if we have Internet access by opening the specified socket.  We  just (as per default parameters) contact google's well-known DNS
    server at an open TCP port:

    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)

    This has multiple advantages over other strategies.  App-layer techniques like
    a urllib2.urlopen('google.com') call require DNS resolution.  Not using ICMP
    avoids packet loss due to overly-locked down secure network environments.

    Taken from http://stackoverflow.com/questions/3764291/checking-network-connection

    :returns: True if connection successful, False if not
    """

    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True

    except Exception as ex:
        print ex.message
        return False