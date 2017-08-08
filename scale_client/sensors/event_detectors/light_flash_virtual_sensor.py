from scale_client.sensors.virtual_sensor import VirtualSensor
# from scale_client.sensors.light_virtual_sensor import LightPhysicalSensor

from time import time as get_time
import logging
log = logging.getLogger(__name__)


class LightFlashVirtualSensor(VirtualSensor):
    def __init__(self, broker, flash_delta=600, event_type="light_flash", **kwargs):
        super(LightFlashVirtualSensor, self).__init__(broker=broker, subscriptions=("light",),
                                                      sample_interval=None, event_type=event_type, **kwargs)
        self._flash_delta = flash_delta
        self._last_value = None

    DEFAULT_PRIORITY = 5

    def on_event(self, event, topic):
        """
        This function checks if the sensor has detected a bright flash above some delta value
        since the last reading and publishes a "light_flash" event if so.  Note that this will
        be highly dependent on how often light events are published!
        """
        et = event.event_type
        ed = event.data

        if et != "light":
            return

        if self._last_value is None:
            pass
        elif ed - self._last_value > self._flash_delta:
            new_event = self.make_event(data=ed)
            new_event.condition = {
                    "delta": {
                        "operator": ">",
                        "value": self._flash_delta
                    }
                }
            self.publish(new_event)
        self._last_value = ed

    def policy_check(self, event):
        return False
