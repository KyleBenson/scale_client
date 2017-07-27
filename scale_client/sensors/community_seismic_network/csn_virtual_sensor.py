import re
import os
import subprocess
import sys
import scale_client
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

import logging
log = logging.getLogger(__name__)


class CSNVirtualSensor(ThreadedVirtualSensor):
    def __init__(self, broker, device=None, **kwargs):
        super(CSNVirtualSensor, self).__init__(broker, device, **kwargs)
        self._reading_regexp = re.compile(r'.*readings: ([\-\+]?[0-9]*(\.[0-9]+)?)')
        self._magic_ln_regexp = re.compile(self.SCALE_VS_MAGIC_LN)

        scale_client_path = os.path.dirname(scale_client.__file__)
        self._virtual_server = scale_client_path + "/sensors/virtual_csn_server/main.py"
        self._result = None

    DEFAULT_PRIORITY = 4
    SCALE_VS_MAGIC_LN = r"\$\$\$_SCALE_VS_MAGIC_LN_\$\$\$"

    def get_type(self):
        return "seismic"

    def on_start(self):
        # TODO: asynchronous callback when something is actually available on this pipe
        self._result = subprocess.Popen(
            [sys.executable, self._virtual_server],
            shell=False,
            stdout=subprocess.PIPE
        )
        super(CSNVirtualSensor, self).on_start()

    def read_raw(self):
        readings = []
        for ln in iter(self._result.stdout.readline, ''):
            log.debug("Line: " + ln.rstrip())
            magic_ln_match = self._magic_ln_regexp.match(ln.rstrip())
            if magic_ln_match:
                break
            else:
                reading_match = self._reading_regexp.match(ln)
                if reading_match:
                    readings.append(float(reading_match.group(1)))

        return readings

    def policy_check(self, data):
        data = data.get_raw_data()
        if len(data) < 3:
            if len(data) > 0:
                log.warn("Not sure why there are less than 3 components to the CSN reading")
            return False
        return True
