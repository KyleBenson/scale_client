from __future__ import print_function

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class LightVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None, threshold=24.0, flash_delta=600):
        super(LightVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port)
        self._threshold = threshold
        self._state = LightVirtualSensor.DARK
        self._flash_delta = flash_delta
        self._last_data = None

    DARK = 0
    BRIGHT = 1

    def get_type(self):
        return "light"

    def read(self):
        event = super(LightVirtualSensor, self).read()
        event.data['condition'] = self.__get_condition()
        return event

    def __get_condition(self):
        if self._state == LightVirtualSensor.DARK:
            return {"threshold": {
                "operator": ">",
                "value": self._threshold
                }
            }
        elif self._state == LightVirtualSensor.BRIGHT:
            return {"threshold": {
                "operator": "<",
                "value": self._threshold
                }
            }

    def policy_check(self, data):
        """
        Only report the data if the light level has transitioned from light to dark or vice-versa.  This function also
        checks if the sensor has detected a bright flash above some delta value since the last reading and publishes a
        "light_flash" event if so.
        :param data: SensedEvent to check
        :return bool:
        """
        data = float(data.get_raw_data())
        success = False

        if self._state == LightVirtualSensor.DARK and data > self._threshold:
            self._state = LightVirtualSensor.BRIGHT
            success = True
        elif self._state == LightVirtualSensor.BRIGHT and data < self._threshold:
            self._state = LightVirtualSensor.DARK
            success = True

        # Flash light detection.  Note that it doesn't require crossing the threshold.
        if self._last_data is not None:
            if (data-self._last_data) > self._flash_delta:
                self.publish(
                    SensedEvent(
                        sensor=self.device.device,
                        data={
                            "event": "light_flash",
                            "value": (data-self._last_data),
                            "condition": {
                                "delta": {
                                    "operator": ">",
                                    "value": self._flash_delta
                                }
                            }
                        },
                        priority=7
                    )
                )
        self._last_data = data
        return success
