import re
import os
import subprocess
import sys
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

import logging
log = logging.getLogger(__name__)

class CsnSensor(ThreadedVirtualSensor):
    """
    This sensor gathers 'picks', which are aperiodic events indicative of a possible earthquake as evidenced by a significant increase in the shaking felt by the accelerometer the CSN client daemon monitors.  The CSN client should be running on this platform with the proper 'hacky' configuration: using a modified `/etc/hosts` file, we trick the CSN client daemon into reporting its picks to `localhost(127.0.0.1)`.  We run a stripped-down version of their server with none of the earthquake-analysis logic that receives the pick and passes it as a SensedEvent into the SCALE client for internal publishing.  In this manner, we're basically using their local event-detection algorithm completely unmodified and running that data through our IoT system.  The client daemon is available in the `csn_bin` folder at the root of this repo.

    While not truly a VirtualSensor, it does make use of periodically reading output from the virtual server.
    We did this solely for the simplicity of implementing it...
    """
    def __init__(self, broker, **kwargs):
        super(CsnSensor, self).__init__(broker, **kwargs)
        self._reading_regexp = re.compile(r'.*readings: ([\-\+]?[0-9]*(\.[0-9]+)?)')
        self._magic_ln_regexp = re.compile(self.SCALE_VS_MAGIC_LN)

        self._virtual_server = os.path.join(os.path.dirname(os.path.abspath(__file__)), "virtual_csn_server", "main.py")
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
        super(CsnSensor, self).on_start()

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
