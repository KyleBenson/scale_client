from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor


# TODO: document the purpose of this class.  How/why is it different from its parent?
class RawAnalogVirtualSensor(AnalogVirtualSensor):

    DEFAULT_PRIORITY = 9

    def get_type(self):
        return "raw_analog"

    def policy_check(self, data):
        return True
