from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class HeartbeatVirtualSensor(VirtualSensor):
    """
    This sensor simply publishes a heartbeat event every interval seconds.
    """

    def get_type(self):
        return "heartbeat"

    def read_raw(self):
        # log.debug("Heartbeat read")
        return "heartbeat"

    def read(self):
    	raw = self.read_raw()
    	event = self.make_event_with_raw_data(raw, priority=10)
    	return event
