from scale_client.sensors.virtual_sensor import VirtualSensor
# from scale_client.sensors.light_virtual_sensor import LightVirtualSensor

from time import time as get_time
import logging
log = logging.getLogger(__name__)


class LightFlashVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, flash_delta=600):
        super(LightFlashVirtualSensor, self).__init__(self, broker=broker, device=device, interval=None)
        self._flash_delta = flash_delta
        self._last_value = None

    def get_type(self):
        return "light_flash"

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et != "light":
            return

        if self._last_value is None:
            pass
        elif ed - self._last_value > self._flash_delta:
            new_event = self.make_event_with_raw_data(raw, priority=7)
            new_event.data["condition"] = {
                    "delta": {
                        "operator": ">",
                        "value": self._flash_delta
                    }
                }
            self.publish(new_event)
        self._last_value = ed

    def policy_check(self, event):
        return False
