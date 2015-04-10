from time import time as get_time

from scale_client.sensors.gpio_virtual_sensor import GPIOVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class PIRVirtualSensor(GPIOVirtualSensor):
    def __init__(self, broker, device=None, interval=1, gpio_pin=None, inact_threshold=600):
        GPIOVirtualSensor.__init__(self, broker, device, interval, gpio_pin)
        self._state = PIRVirtualSensor.IDLE
        self._inact_timer = get_time()
        self._inact_threshold = inact_threshold

    IDLE = 0
    ACTIVE = 1

    def get_type(self):
        return "motion"

    def policy_check(self, data):
        data = data.get_raw_data()
        should_report = False

        # State transitions
        if self._state == PIRVirtualSensor.IDLE and data == PIRVirtualSensor.ACTIVE:
            self._state = PIRVirtualSensor.ACTIVE
            should_report = True
        elif self._state == PIRVirtualSensor.ACTIVE and data == PIRVirtualSensor.IDLE:
            self._state = PIRVirtualSensor.IDLE
            self._inact_timer = get_time()
            should_report = True

        # Here we check if the sensor has not been active for some time period, in which case we publish a different
        # type of event to notify that this sensor is still active
        elif self._state == PIRVirtualSensor.IDLE and (get_time() - self._inact_timer) > self._inact_threshold:
            self.publish(
                    SensedEvent(
                        sensor=self.device.device,
                        data={
                        "event": self.get_type(),
                        "value": data,
                        "condition": {
                        "inactive_time": {
                        "operator": ">",
                        "value": self._inact_threshold
                        }
                        }
                        },
                        priority=7
                    )
                )
            self._inact_timer = get_time()

        return should_report
