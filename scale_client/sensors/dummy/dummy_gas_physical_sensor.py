from random import *

from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor
from scale_client.sensors.environment.gas_physical_sensor import GasPhysicalSensor
from dummy_physical_sensor import DummyPhysicalSensor


class DummyGasPhysicalSensor(GasPhysicalSensor, DummyPhysicalSensor):
    def __init__(self, broker, prob=0.05, **kwargs):
        self._rand = Random()
        # we aren't specifying an analog port as the on_start() override takes care of avoiding the check for a legit 1
        super(DummyGasPhysicalSensor, self).__init__(broker, **kwargs)
        self._rand.seed()
        self._prob = prob
        self._darkflag = True
        self._dummyval = DummyGasPhysicalSensor.DRK_MEAN

    DRK_MEAN = 200
    BRT_MEAN = 800

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parents
        super(AnalogPhysicalSensor, self).on_start()

    def read_raw(self):
        if self._rand.random() < self._prob:
            self._darkflag = not self._darkflag
        if self._darkflag:
            self._dummyval = int(self._dummyval * 0.5 + DummyGasPhysicalSensor.DRK_MEAN * 0.5)
        else:
            self._dummyval = DummyGasPhysicalSensor.BRT_MEAN
            self._darkflag = not self._darkflag
        return self._dummyval
