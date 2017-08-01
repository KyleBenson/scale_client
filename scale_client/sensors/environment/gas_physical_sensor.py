from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor


class GasPhysicalSensor(AnalogPhysicalSensor):
    def __init__(self, broker, interval=1, threshold=400, gas_type=None, **kwargs):
        super(GasPhysicalSensor, self).__init__(broker, interval=interval, **kwargs)
        self._threshold = threshold
        self._gas_type = gas_type

    DEFAULT_PRIORITY = 3

    def get_type(self):
        if type(self._gas_type) == type(""):
            return self._gas_type
        return "explosive_gas"

    def read(self):
        event = super(GasPhysicalSensor, self).read()
        event.data['condition'] = {
                "threshold": {
                    "operator": ">",
                    "value": self._threshold
                }
            }
        return event

    def policy_check(self, data):
        return float(data.get_raw_data()) > self._threshold
