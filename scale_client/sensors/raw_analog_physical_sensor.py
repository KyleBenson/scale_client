from scale_client.sensors.analog_physical_sensor import AnalogPhysicalSensor


# TODO: document the purpose of this class.  How/why is it different from its parent?
class RawAnalogPhysicalSensor(AnalogPhysicalSensor):

    DEFAULT_PRIORITY = 9

    def policy_check(self, data):
        return True
