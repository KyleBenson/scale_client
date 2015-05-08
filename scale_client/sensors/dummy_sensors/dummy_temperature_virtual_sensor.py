from random import *

from scale_client.sensors.temperature_virtual_sensor import TemperatureVirtualSensor


class DummyTemperatureVirtualSensor(TemperatureVirtualSensor):
    def __init__(self, broker, device=None, threshold=24.0):
        TemperatureVirtualSensor.__init__(self, broker, device=device, threshold=threshold)
        self._rand = Random()
        self._rand.seed()
        self._darkflag = True
        self.CEL_MEAN = threshold

    def read_raw(self):
        return round(self.CEL_MEAN + self._rand.random() * 12 - 6, 2)

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parent
        super(TemperatureVirtualSensor, self).on_start()
