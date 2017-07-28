from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class HeartbeatVirtualSensor(VirtualSensor):
    """
    This sensor simply publishes a heartbeat event every interval seconds.
    """
    def get_type(self):
        return "heartbeat"

    DEFAULT_PRIORITY = 10

    def read_raw(self):
        return "heartbeat"
