from __future__ import print_function

from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor


class LightPhysicalSensor(AnalogPhysicalSensor):
    def __init__(self, broker, interval=1, threshold=400, **kwargs):
        super(LightPhysicalSensor, self).__init__(broker, interval=interval, **kwargs)
        self._threshold = threshold
        # TODO: this should probably start in a None state so that the first reading is always published with its true state; otherwise we might be left in the dark forever...
        self._state = LightPhysicalSensor.DARK

    DEFAULT_PRIORITY = 7
    DARK = 0
    BRIGHT = 1

    def get_type(self):
        return "light"

    def read(self):
        event = super(LightPhysicalSensor, self).read()
        event.data['condition'] = self.__get_condition()
        return event

    def __get_condition(self):
        if self._state == LightPhysicalSensor.DARK:
            return {"threshold": {
                        "operator": ">",
                        "value": self._threshold
                    }
                }
        elif self._state == LightPhysicalSensor.BRIGHT:
            return {"threshold": {
                        "operator": "<",
                        "value": self._threshold
                    }
                }

    def policy_check(self, data):
        """
        Only report the data if the light level has transitioned from light to dark or vice-versa.
        :param data: SensedEvent to check
        :return bool:
        """
        raw = float(data.get_raw_data())
        success = False

        if self._state == LightPhysicalSensor.DARK and raw > self._threshold:
            self._state = LightPhysicalSensor.BRIGHT
            success = True
        elif self._state == LightPhysicalSensor.BRIGHT and raw < self._threshold:
            self._state = LightPhysicalSensor.DARK
            success = True
        return success
