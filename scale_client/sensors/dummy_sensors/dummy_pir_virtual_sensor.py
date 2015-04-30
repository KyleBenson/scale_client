from random import *

from scale_client.sensors.pir_virtual_sensor import PIRVirtualSensor
from scale_client.sensors.virtual_sensor import VirtualSensor


class DummyPIRVirtualSensor(PIRVirtualSensor):
    def __init__(self, broker, device):
        super(DummyPIRVirtualSensor, self).__init__(broker, device)
        self._rand = Random()
        self._rand.seed()
        self._darkflag = True

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parent
        VirtualSensor.on_start(self)

    def read_raw(self):
        if self._rand.random() < 0.1:
            self._darkflag = not self._darkflag
        if self._darkflag:
            return 0
        else:
            return 1
