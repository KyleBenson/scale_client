import subprocess
import re

from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)


class TemperatureVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, threshold=24.0, daemon_path='temperature-streams'):
        super(TemperatureVirtualSensor, self).__init__(broker, device)
        self._daemon_path = daemon_path
        self._threshold = threshold
        self._result = None
        self._regexp = re.compile(r'Device ([^:]*): Sensor ([0-9]*): Temperature: ([0-9\.]*)')

    DEFAULT_PRIORITY = 5

    def get_type(self):
        return "temperature"

    def on_start(self):
        self._result = subprocess.Popen(
            [self._daemon_path],
            shell=True,
            stdout=subprocess.PIPE
        )

    def read_raw(self):
        line = next(iter(self._result.stdout.readline, ''))
        match = self._regexp.match(line)
        try:
            temperature = float(match.group(3))
        except AttributeError as e:
            log.error('Error parsing temperature: %s' % e)

        return temperature

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
