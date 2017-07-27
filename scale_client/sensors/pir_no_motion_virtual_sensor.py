from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.sensors.pir_virtual_sensor import PIRVirtualSensor

from time import time as get_time
import logging
log = logging.getLogger(__name__)


class PIRNoMotionVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, interval=1, inact_threshold=600, **kwargs):
        super(PIRNoMotionVirtualSensor, self).__init__(broker=broker, device=device, interval=interval, **kwargs)
        self._inact_timer = get_time()
        self._inact_threshold = inact_threshold

    DEFAULT_PRIORITY = 7

    def get_type(self):
        return "no_motion"

    def read_raw(self):
        return PIRVirtualSensor.IDLE

    def read(self):
        event = super(PIRNoMotionVirtualSensor, self).read()
        event.data["condition"] = self.__get_condition()
        return event

    def __get_condition(self):
        return{"inactive_time": {
                    "operator": ">",
                    "value": self._inact_threshold
                }
            }

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et != "motion":
            return

        if ed == PIRVirtualSensor.IDLE:
            self._inact_timer = get_time()
        else:
            self._inact_timer = None

    def policy_check(self, event):
        if self._inact_timer is not None:
            if self._inact_timer + self._inact_threshold < get_time():
                self._inact_timer = get_time()
                return True
        return False
