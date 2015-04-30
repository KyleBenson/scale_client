from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.sensors.pir_virtual_sensor import PIRVirtualSensor

from time import time as get_time
import logging
log = logging.getLogger(__name__)


class PIRNoMotionVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, inact_threshold=600):
        super(PIRNoMotionVirtualSensor, self).__init__(broker=broker, device=device, interval=None)
        self._inact_timer = None
        self._inact_threshold = inact_threshold

    def get_type(self):
        return "no_motion"

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et != "motion":
            return

        if ed == PIRVirtualSensor.IDLE:
            if self._inact_timer is None:
                self._inact_timer = get_time()
            elif self._inact_timer + self.inact_threshold < get_time():
                new_event = self.make_event_with_raw_data(raw, priority=7)
                new_event.data["condition"] = {
                        "inactive_time": {
                            "operator": ">",
                            "value": self._inact_threshold
                        }
                    }
                self.publish(new_event)
                self._inact_timer = get_time()
        elif ed == PIRVirtualSensor.ACTIVE:
            self._inact_timer = None

    def policy_check(self, event):
        return False
