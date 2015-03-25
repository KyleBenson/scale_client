from scale_client.sensors.virtual_sensor import VirtualSensor


class HeartbeatVirtualSensor(VirtualSensor):
    """
    This sensor simply publishes a heartbeat event every interval seconds.
    """

    def get_type(self):
        return "heartbeat"

    def read_raw(self):
        return "heartbeat"