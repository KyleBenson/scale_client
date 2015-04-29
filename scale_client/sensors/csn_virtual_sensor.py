import re
import subprocess
from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)

SCALE_VS_MAGIC_LN = r"\$\$\$_SCALE_VS_MAGIC_LN_\$\$\$"


class CSNVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None):
        super(CSNVirtualSensor, self).__init__(broker, device)
        self._reading_regexp = re.compile(r'.*readings: ([\-\+]?[0-9]*(\.[0-9]+)?)')
        self._magic_ln_regexp = re.compile(SCALE_VS_MAGIC_LN)
        self._result = None

    def get_type(self):
        return "seismic"

    def on_start(self):
        # TODO: asynchronous callback when something is actually available on this pipe
        self._result = subprocess.Popen(
            ["/root/SmartAmericaSensors/scale_client/virtual_csn_server/main.py"],
            shell=True,
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
            log.warn("Not sure why there are less than 3 components to the CSN reading")
            return False
        return True
