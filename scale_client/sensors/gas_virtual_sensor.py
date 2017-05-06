from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor


class GasVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None, threshold=400, gas_type=None, **kwargs):
        super(GasVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port, **kwargs)
        self._threshold = threshold
        self._gas_type = gas_type

    DEFAULT_PRIORITY = 3

    def get_type(self):
        if type(self._gas_type) == type(""):
            return self._gas_type
        return "explosive_gas"

    def read(self):
        event = super(GasVirtualSensor, self).read()
        event.data['condition'] = {
                "threshold": {
                    "operator": ">",
                    "value": self._threshold
                }
            }
        return event

    def policy_check(self, data):
        return float(data.get_raw_data()) > self._threshold
