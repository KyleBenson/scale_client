from random import *

from scale_client.sensors.gas_virtual_sensor import GasVirtualSensor
from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor


class DummyGasVirtualSensor(GasVirtualSensor):
    def __init__(self, broker, device=None, interval=1, threshold=400, prob=0.05):
        self._rand = Random()
        # we aren't specifying an analog port as the on_start() override takes care of avoiding the check for a legit 1
        super(DummyGasVirtualSensor, self).__init__(broker, device=device, interval=interval, threshold=threshold)
        self._rand.seed()
        self._prob = prob
        self._darkflag = True
        self._dummyval = DummyGasVirtualSensor.DRK_MEAN

    DRK_MEAN = 200
    BRT_MEAN = 800

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parents
        super(AnalogVirtualSensor, self).on_start()

    def read_raw(self):
        if self._rand.random() < self._prob:
            self._darkflag = not self._darkflag
        if self._darkflag:
            self._dummyval = int(self._dummyval * 0.5 + DummyGasVirtualSensor.DRK_MEAN * 0.5)
        else:
            self._dummyval = DummyGasVirtualSensor.BRT_MEAN
            self._darkflag = not self._darkflag
        return self._dummyval
