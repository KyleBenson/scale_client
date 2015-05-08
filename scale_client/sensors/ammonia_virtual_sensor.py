from scale_client.sensors.n5_resistor_virtual_sensor import N5ResistorVirtualSensor


class AmmoniaVirtualSensor(N5ResistorVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None, threshold=1.0):
        super(AmmoniaVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port)
        self._threshold = threshold

    DEFAULT_PRIORITY = 4

    def get_type(self):
        return "ammonia"

    def read(self):
        event = super(AmmoniaVirtualSensor, self).read()
        event.data['condition'] = {
                "threshold": {
                    "operator": "<",
                    "value": self._threshold
                }
            }
        return event

    def policy_check(self, data):
    	raw = data.get_raw_data()
    	if raw is not None:
        	return raw > self._threshold