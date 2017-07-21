import time
from random import *

from scale_client.sensors.csn_virtual_sensor import CSNVirtualSensor
from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class DummyCSNVirtualSensor(CSNVirtualSensor):
    def __init__(self, broker, device="dummy_csn", **kwargs):
        super(DummyCSNVirtualSensor, self).__init__(broker, device=device, **kwargs)
        self._rand = Random()
        self._rand.seed()
        self._whatflag = True

    WAIT_MEAN = 10

    def on_start(self):
        # Avoid opening any connections to real sensors, so skip the on_start() of our parent
        # and instead run this dummy sensor as a regular non-threaded VS.
        VirtualSensor.on_start(self)

    def read_raw(self):
        readings = []
        if self._whatflag:
            readings.append(self._rand.random() * 0.1)
            readings.append(self._rand.random() * 0.1)
            readings.append(0.0)
        else:
            readings.append(0.0)
            readings.append(0.0)
            readings.append(self._rand.random() * 0.1)
        self._whatflag = not self._whatflag

        # reset the timer to a random time so that events appear more dynamically
        # NOTE: this relies on the set_wait_period API implementation resetting
        # the timer immediately!  consider it a hack!
        wait_time = self._rand.random() * 2 * DummyCSNVirtualSensor.WAIT_MEAN
        print "waiting for:", wait_time
        self.set_wait_period(wait_time)
        return readings
