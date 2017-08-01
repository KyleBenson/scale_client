from random import *

from scale_client.sensors.environment.temperature_physical_sensor import TemperaturePhysicalSensor
from dummy_physical_sensor import DummyPhysicalSensor

class DummyTemperaturePhysicalSensor(TemperaturePhysicalSensor, DummyPhysicalSensor):
    def __init__(self, broker, **kwargs):
        super(DummyTemperaturePhysicalSensor, self).__init__(broker=broker, **kwargs)
        self._rand = Random()
        self._rand.seed()
        self.CEL_MEAN = self._threshold

    def read_raw(self):
        return round(self.CEL_MEAN + self._rand.random() * 12 - 6, 2)
