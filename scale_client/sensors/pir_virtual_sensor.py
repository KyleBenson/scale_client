from time import time as get_time

from scale_client.sensors.gpio_virtual_sensor import GPIOVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class PIRVirtualSensor(GPIOVirtualSensor):
    def __init__(self, broker, device=None, interval=1, gpio_pin=None):
        super(PIRVirtualSensor, self).__init__(broker, device, interval, gpio_pin)
        self._state = PIRVirtualSensor.IDLE

    DEFAULT_PRIORITY = 7
    IDLE = 0
    ACTIVE = 1

    def get_type(self):
        return "motion"

    def policy_check(self, data):
        raw = data.get_raw_data()
        success = False

        # State transitions
        if self._state == PIRVirtualSensor.IDLE and raw == PIRVirtualSensor.ACTIVE:
            self._state = PIRVirtualSensor.ACTIVE
            success = True
        elif self._state == PIRVirtualSensor.ACTIVE and raw == PIRVirtualSensor.IDLE:
            self._state = PIRVirtualSensor.IDLE
            # self._inact_timer = get_time()
            success = True

        return success
