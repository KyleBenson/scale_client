from random import *

from scale_client.sensors.environment.pir_physical_sensor import PirPhysicalSensor
from scale_client.sensors.gpio_physical_sensor import GpioPhysicalSensor
from dummy_physical_sensor import DummyPhysicalSensor


class DummyPirPhysicalSensor(PirPhysicalSensor, DummyPhysicalSensor):
    def __init__(self, broker, **kwargs):
        super(DummyPirPhysicalSensor, self).__init__(broker, **kwargs)
        self._rand = Random()
        self._rand.seed()
        self._darkflag = True

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parent
        super(GpioPhysicalSensor, self).on_start()

    def read_raw(self):
        if self._rand.random() < 0.1:
            self._darkflag = not self._darkflag
        if self._darkflag:
            return 0
        else:
            return 1
