import logging
from time import time as get_time

from scale_client.sensors.environment.pir_physical_sensor import PirPhysicalSensor
from scale_client.sensors.virtual_sensor import VirtualSensor

log = logging.getLogger(__name__)


class NoMotionVirtualSensor(VirtualSensor):
    def __init__(self, broker, sample_interval=1, inact_threshold=600, event_type="no_motion", **kwargs):
        super(NoMotionVirtualSensor, self).__init__(broker=broker, subscriptions=("motion",),
                                                    sample_interval=sample_interval, event_type=event_type, **kwargs)
        self._inact_timer = get_time()
        self._inact_threshold = inact_threshold

    DEFAULT_PRIORITY = 7

    def read_raw(self):
        return PirPhysicalSensor.IDLE

    def read(self):
        event = super(NoMotionVirtualSensor, self).read()
        event.condition = self.__get_condition()
        return event

    def __get_condition(self):
        return{"inactive_time": {
                    "operator": ">",
                    "value": self._inact_threshold
                }
            }

    def on_event(self, event, topic):
        et = event.event_type
        ed = event.data

        if et != "motion":
            return

        if ed == PirPhysicalSensor.IDLE:
            self._inact_timer = get_time()
        else:
            self._inact_timer = None

    def policy_check(self, event):
        if self._inact_timer is not None:
            if self._inact_timer + self._inact_threshold < get_time():
                self._inact_timer = get_time()
                return True
        return False
