from virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class TemperatureVirtualSensor(VirtualSensor):
    """
    Temperature sensor that only reports data when it's above some threshold.
    """
    def __init__(self, broker, device=None, interval=1, threshold=24.0, **kwargs):
        super(TemperatureVirtualSensor, self).__init__(broker, device, interval=interval, **kwargs)
        self._threshold = threshold

    DEFAULT_PRIORITY = 5

    def get_type(self):
        return "temperature"

    def read(self):
        event = super(TemperatureVirtualSensor, self).read()
        event.data['condition'] = {
            "threshold": {
                "operator": ">",
                "value": self._threshold
            }
        }

        return event

    def policy_check(self, event):
        return event.data['value'] > self._threshold
