from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class TemperatureHighVirtualSensor(VirtualSensor):
    def __init__(self, broker, threshold=28.0, **kwargs):
        super(TemperatureHighVirtualSensor, self).__init__(broker=broker, subscriptions=("temperature",),
                                                           sample_interval=None, **kwargs)
        self._threshold = threshold

    DEFAULT_PRIORITY = 4

    def get_type(self):
        return "temperature_high"

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et != "temperature":
            return

        if ed > self._threshold:
            new_event = self.make_event_with_raw_data(ed)
            new_event.data["condition"] = {
                    "threshold": {
                        "operator": ">",
                        "value": self._threshold
                    }
                }
            self.publish(new_event)

    def policy_check(self, event):
        return False
