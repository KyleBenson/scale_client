from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class TemperatureHighVirtualSensor(VirtualSensor):
    def __init__(self, broker, threshold=28.0, event_type="temperature_high", **kwargs):
        super(TemperatureHighVirtualSensor, self).__init__(broker=broker, subscriptions=("temperature",),
                                                           sample_interval=None, event_type=event_type, **kwargs)
        self._threshold = threshold

    DEFAULT_PRIORITY = 4

    def on_event(self, event, topic):
        et = event.event_type
        ed = event.data

        if et != "temperature":
            return

        if ed > self._threshold:
            new_event = self.make_event(data=ed)
            new_event.condition = {
                    "threshold": {
                        "operator": ">",
                        "value": self._threshold
                    }
                }
            self.publish(new_event)

    def policy_check(self, event):
        return False
