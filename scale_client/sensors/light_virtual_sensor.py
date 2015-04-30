from __future__ import print_function

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class LightVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None, threshold=400):
        super(LightVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port)
        self._threshold = threshold
        self._state = LightVirtualSensor.DARK

    DEFAULT_PRIORITY = 7
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
        raw = float(data.get_raw_data())
        success = False

        if self._state == LightVirtualSensor.DARK and raw > self._threshold:
            self._state = LightVirtualSensor.BRIGHT
            success = True
        elif self._state == LightVirtualSensor.BRIGHT and raw < self._threshold:
            self._state = LightVirtualSensor.DARK
            success = True
        return success
