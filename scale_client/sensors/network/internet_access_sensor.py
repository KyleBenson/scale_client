from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor
from scale_client.networks.util import ping_internet

from time import time as get_time
import logging
log = logging.getLogger(__name__)

class InternetAccessSensor(ThreadedVirtualSensor):
    """
    Network sensor that 'pings' the Internet periodically and publishes
    events when the connection status changes as well as every so many
    seconds. Note that it simply calls out to a util class, so only
    bother changing the default parameters if you really need to.
    It uses a UDP/DNS probe for better performance than anything TCP-based
    while still being able to circumvent most firewalls.
    """

    def __init__(self, broker, sample_interval=10, report_every=60,
                 # Taken directly from net.util.ping_interet():
                 host="8.8.8.8", port=53, timeout=3,
                 event_type="internet_access", **kwargs):
        """
        :param broker:
        :param sample_interval: defaults to 10 seconds
        :param report_every: policy_check will return True at least every this many secs
        :param host: host to 'ping' (default is Google DNS server)
        :param port: port to 'ping' (default is DNS)
        :param timeout: timeout for 'ping'
        """

        super(InternetAccessSensor, self).__init__(broker, sample_interval=sample_interval,
                                                   event_type=event_type, **kwargs)
        self._last_value = None
        self._last_report_time = None
        self._report_every = report_every

        self._host_to_ping = host
        self._port = port
        self._timeout = timeout

    DEFAULT_PRIORITY = 8

    def read_raw(self):
        return ping_internet(host=self._host_to_ping, port=self._port, timeout=self._timeout)

    def policy_check(self, event):
        raw = event.data
        success = False

        # Conditionally report data
        first_attempt = self._last_report_time is None
        value_changed = not first_attempt and raw != self._last_value
        timer_expired = not first_attempt and (self._last_report_time + self._report_every < get_time())

        if first_attempt or value_changed or timer_expired:
            self._last_report_time = get_time()
            log.debug("We %s have Internet access!" % ("DO" if raw else "DO NOT"))
            success = True

        self._last_value = raw

        return success
