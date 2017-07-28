from random import *

from scale_client.sensors.environment.temperature_virtual_sensor import TemperatureVirtualSensor


class DummyTemperatureVirtualSensor(TemperatureVirtualSensor):
    def __init__(self, broker, device=None, threshold=24.0, **kwargs):
        super(DummyTemperatureVirtualSensor, self).__init__(broker=broker, device=device, threshold=threshold, **kwargs)
        self._rand = Random()
        self._rand.seed()
        self.CEL_MEAN = threshold

    def read_raw(self):
        return round(self.CEL_MEAN + self._rand.random() * 12 - 6, 2)
