from temperature_physical_sensor import TemperaturePhysicalSensor

import time
# TODO: perhaps separate out some of the USB logic so we can make a UsbPhysicalSensor class?
from usb.core import USBError
from temperusb import TemperHandler
import logging
log = logging.getLogger(__name__)


class UsbTemperaturePhysicalSensor(TemperaturePhysicalSensor):
    """
    This class connects to a USB temperature sensor that supports the 'TEMPered' USB driver.
    """
    def __init__(self, broker, threshold=24.0, search_interval=60, **kwargs):
        super(TemperaturePhysicalSensor, self).__init__(broker, **kwargs)
        self._threshold = threshold
        self._search_interval = search_interval

        self._devs = None
        self._curr_dev = None
        self._dev_timer = None

    def on_start(self):
        self._get_devices()
        super(TemperaturePhysicalSensor, self).on_start()

    def _get_devices(self):
        self._devs = TemperHandler().get_devices()
        log.info("found %d device(s)" % len(self._devs))

    def read_raw(self):
        if self._curr_dev is None:
            raise NotImplementedError
        return round(self._curr_dev.get_temperature(), 2)

    def read(self):
        event = super(UsbTemperaturePhysicalSensor, self).read()
        event.condition = {
                "threshold": {
                    "operator": ">",
                    "value": self._threshold
                }
            }

        return event

    def _do_sensor_read(self):
        if len(self._devs) < 1:
            if self._dev_timer is None or self._dev_timer + self._search_interval < time.time():
                self._get_devices()
                self._dev_timer = time.time()
            return

        self._dev_timer = None
        log.debug("%s reading sensor data..." % self.name)
        # XXX: seems like we iterate over multiple possible available devices, but a Sensor should
        # only be associated with a single device... Instead (if we choose to continue using the USB
        # sensor) we should put this for loop in read() and handle the error there instead of
        # passing a device reference around, which violates the API.
        for dev in self._devs:
            try:
                self._curr_dev = dev
                event = self.read()
            except USBError:
                log.warning("device disconnected")
                self._get_devices()
                break
            if event is None:
                continue
            if self.policy_check(event):
                self.publish(event)
