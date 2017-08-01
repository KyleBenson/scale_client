from random import *

from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor
from scale_client.sensors.environment.light_physical_sensor import LightPhysicalSensor
from dummy_physical_sensor import DummyPhysicalSensor


class DummyLightPhysicalSensor(LightPhysicalSensor, DummyPhysicalSensor):
    def __init__(self, broker, **kwargs):
        super(DummyLightPhysicalSensor, self).__init__(broker, **kwargs)
        self._rand = Random()
        self._rand.seed()
        self._darkflag = True

    DRK_MEAN = 20
    BRT_MEAN = 1000

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parents
        super(AnalogPhysicalSensor, self).on_start()

    def read_raw(self):
        if self._rand.random() < 0.05:
            self._darkflag = not self._darkflag
        if self._darkflag:
            return DummyLightPhysicalSensor.DRK_MEAN
        else:
            return DummyLightPhysicalSensor.BRT_MEAN
