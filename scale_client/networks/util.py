"""
Various network-related utility functions to be used by apps.
"""

import time
import socket
import logging
log = logging.getLogger(__name__)

from scale_client.core.sensed_event import SensedEvent
from ..util import uri


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

    # TODO: UDP support?
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True

    except Exception as ex:
        log.debug("internet ping failed with error: %s" % ex.message)
        return False

def process_remote_event(event, protocol=None, hostname=None, port=None, relay_uri=None):
    """
    Process a SensedEvent from a remote node by:
    1) ensuring its source points to the remote that created it,
    2) saving the time this event was received (right now)
    3) optionally storing the relay_uri we received this event from e.g. resource URI (if different from remote URI), broker URI, etc.
    NOTE: if relay_uri is specified but the other parameters are not, they'll be extracted from relay_uri so
        you'll need to either set relay_uri or at least hostname/port!
    :param event:
    :type event: scale_client.core.SensedEvent
    :param hostname: the remote host
    :param port: remote port from which the event came
    :param relay_uri: optional URI specifying the remote entity from which this event just came
        (e.g. broker or CoAP resource) as opposed to the entity that originally created it
    :param protocol: name of the protocol to include in the URI
    """

    # If the event isn't already formatted as from a legitimate remote source (i.e. remote forgot to convert the source),
    # tag it as coming from the specified remote so we don't interpret it as a local one and e.g. send it back there.
    if event.is_local or not uri.is_host_known(event.source):
        # try to extract unspecified parameters
        parsed_relay_uri = uri.parse_uri(relay_uri) if relay_uri is not None else None
        if parsed_relay_uri and not hostname:
            hostname = parsed_relay_uri.host
        if parsed_relay_uri and not port:
            port = parsed_relay_uri.port
        if parsed_relay_uri and not protocol:
            protocol = parsed_relay_uri.getscheme()

        # verify we have enough information to proceed
        if not hostname or not (port or protocol):
            raise ValueError("failed to specify enough fields to at least identify protocol/port and host!"
                             " host=%s, port=%s, protocol=%s, relay_uri=%s" % (hostname, port, protocol, relay_uri))

        # ENHANCE: perhaps we want to allow remote to specify a different protocol without knowing its IP address?
        # ENHANCE: perhaps we should do some validation as some networks could make this a problem e.g. a NAT
        event.source = uri.get_remote_uri(event.source, protocol=protocol, host=hostname, port=port)

    # Assume the receive time is right now:
    event.metadata.setdefault('time_rcvd', SensedEvent.get_timestamp())

    # In case the remote's original URI is different than how we got it from the CoAP resource:
    if relay_uri and relay_uri != event.source:
        event.metadata.setdefault('relay_uri', relay_uri)


# CoAP-related stuff


from coapthon.defines import Codes as CoapCodes
def coap_response_success(resp):
    return resp.code < CoapCodes.ERROR_LOWER_BOUND

def coap_code_to_name(code):
    return CoapCodes.LIST[code].name

from coapthon.defines import COAP_DEFAULT_PORT
DEFAULT_COAP_PORT = COAP_DEFAULT_PORT
# XXX: this value taken from the RFC's recommendations.  coapthon has a hard-coded receiving packet size, hence this...
COAP_MAX_PAYLOAD_SIZE = 1024

def msg_fits_one_coap_packet(msg):
    """Returns True if msg is small enough to fit in a single CoAP packet, False if it's probably too big."""
    return len(msg) <= COAP_MAX_PAYLOAD_SIZE
