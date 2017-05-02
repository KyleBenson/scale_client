from threaded_virtual_sensor import ThreadedVirtualSensor

# from urllib2 import urlopen
import os
from time import time as get_time
import logging
log = logging.getLogger(__name__)


class InternetAccessVirtualSensor(ThreadedVirtualSensor):
    def __init__(self, broker, device=None, interval=5, ping_host="8.8.4.4", timeout=2, _report_threshold=60):
        super(InternetAccessVirtualSensor, self).__init__(broker, device=device, interval=interval)
        self._ping_host = ping_host
        self._last_value = None
        self._report_timer = None
        self._report_threshold = _report_threshold

        if type(timeout) != type(0):
            raise TypeError
        self._timeout = timeout

    DEFAULT_PRIORITY = 8

    def get_type(self):
        return "internet_access"

    def read_raw(self):
        cmd = "ping -c 1 -w %s %s %s" % (self._timeout, self._ping_host, " >/dev/null 2>&1")
        log.debug("running command: %s" % cmd)
        res = os.system(cmd)
        if res != 0:
            return False
        return True

    def policy_check(self, data):
        raw = data.get_raw_data()
        success = False
        if raw != self._last_value or self._report_timer is None or self._report_timer + self._report_threshold < get_time():
            self._report_timer = get_time()
            success = True
        self._last_value = raw

        if success:
            log.info("We %s have Internet access!" % ("DO" if raw else "DO NOT"))

        return success
