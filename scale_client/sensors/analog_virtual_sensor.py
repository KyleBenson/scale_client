from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class AnalogVirtualSensor(VirtualSensor):
    """
    This class is specifically designed to support Analog sensors attached to a ADC board on a Raspberry Pi.
    """

    def __init__(self, broker, device=None, analog_port=None):
        VirtualSensor.__init__(self, broker, device)
        self._port = analog_port
        self._spi = None

    def read_raw(self):
        raw_reading = self._spi.xfer2([1, 8 + self._port << 4, 0])
        adcout = ((raw_reading[1] & 3) << 8) + raw_reading[2]
        return adcout

    def on_start(self):
        if self._port > 3 or self._port < 0 or self._port is None:
            raise ValueError("invalid analog port number")

        if self._spi is None:
            import spidev

            self._spi = spidev.SpiDev()
        try:
            self._spi.open(0, 0)
        except IOError:
            log.error("Failed to open analog device: " + self.device.device)

        super(AnalogVirtualSensor, self).on_start()