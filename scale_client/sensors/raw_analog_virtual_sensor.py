from __future__ import print_function

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class RawAnalogVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None):
        AnalogVirtualSensor.__init__(self, broker, device=device, interval=interval, analog_port=analog_port)

    def get_type(self):
        return "raw_analog"

    def read(self):
        event = super(RawAnalogVirtualSensor, self).read()
        event.data['condition'] = {} #XXX: Do we have to have empty condition?
        return event

    def policy_check(self, data):
        return True
