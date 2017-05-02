from temperature_virtual_sensor import TemperatureVirtualSensor

import time
from usb.core import USBError
from temperusb import TemperHandler
import logging
log = logging.getLogger(__name__)


class UsbTemperatureVirtualSensor(TemperatureVirtualSensor):
    def __init__(self, broker, device=None, interval=1, threshold=24.0, search_interval=60):
        super(TemperatureVirtualSensor, self).__init__(broker, device, interval=interval)
        self._threshold = threshold
        self._search_interval = search_interval

        self._devs = None
        self._curr_dev = None
        self._dev_timer = None

    def on_start(self):
        self._get_devices()
        super(TemperatureVirtualSensor, self).on_start()

    def _get_devices(self):
        self._devs = TemperHandler().get_devices()
        log.info("found %d device(s)" % len(self._devs))

    def read_raw(self):
        if self._curr_dev is None:
            raise NotImplementedError
        return round(self._curr_dev.get_temperature(), 2)

    def read(self):
        event = super(UsbTemperatureVirtualSensor, self).read()
        event.data['condition'] = {
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
        log.debug("%s reading sensor data..." % self.get_type())
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
