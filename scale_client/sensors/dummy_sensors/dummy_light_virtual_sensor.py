from random import *

from scale_client.sensors.light_virtual_sensor import LightVirtualSensor
# from scale_client.sensors.virtual_sensor import VirtualSensor


class DummyLightVirtualSensor(LightVirtualSensor):
    def __init__(self, broker, device=None, interval=1, threshold=400):
        super(DummyLightVirtualSensor, self).__init__(broker, device=device, interval=interval, threshold=threshold)
        self._rand = Random()
        self._rand.seed()
        self._darkflag = True

    DRK_MEAN = 20
    BRT_MEAN = 1000

    def on_start(self):
        # avoid opening any connections to real sensors, so skip the on_start() of our parents
        super(LightVirtualSensor, self).on_start()

    def read_raw(self):
        if self._rand.random() < 0.05:
            self._darkflag = not self._darkflag
        if self._darkflag:
            return DummyLightVirtualSensor.DRK_MEAN
        else:
            return DummyLightVirtualSensor.BRT_MEAN
