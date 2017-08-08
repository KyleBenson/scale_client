from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor


class GasPhysicalSensor(AnalogPhysicalSensor):
    def __init__(self, broker, interval=1, threshold=400, event_type="explosive_gas", **kwargs):
        super(GasPhysicalSensor, self).__init__(broker, interval=interval, event_type=event_type, **kwargs)
        self._threshold = threshold

    DEFAULT_PRIORITY = 3

    def read(self):
        event = super(GasPhysicalSensor, self).read()
        event.condition = {
                "threshold": {
                    "operator": ">",
                    "value": self._threshold
                }
            }
        return event

    def policy_check(self, event):
        return float(event.data) > self._threshold
