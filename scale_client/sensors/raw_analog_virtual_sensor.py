from __future__ import print_function

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class RawAnalogVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None):
        super(RawAnalogVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port)

    def get_type(self):
        return "raw_analog"

    def read(self):
        # event = super(RawAnalogVirtualSensor, self).read()
        raw = self.read_raw()
        event = self.make_event_with_raw_data(raw, priority=9)
        # event.data['condition'] = {}
        return event

    def policy_check(self, data):
        return True
