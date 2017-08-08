from scale_client.sensors.virtual_sensor import VirtualSensor
from gps_poller import GPSPoller

import time
import logging
log = logging.getLogger(__name__)

class GpsSensor(VirtualSensor):
    def __init__(self, broker, interval=5, exp=10, event_type="gps", **kwargs):
        super(GpsSensor, self).__init__(broker, interval=interval, event_type=event_type, **kwargs)
        self._exp = exp
        self._gps_poller = None

    DEFAULT_PRIORITY = 7

    def on_start(self):
        # TODO: this should be done in a self.run_in_background call rather than directly starting a thread,
        # especially a daemon!
        self._gps_poller = GPSPoller()
        self._gps_poller.daemon = True
        self._gps_poller.start()
        super(GpsSensor, self).on_start()

    def read_raw(self):
        if self._gps_poller is None:
            return None
        raw = self._gps_poller.get_dict()
        if type(raw) != type({}):
            return None
        raw["exp"] = time.time() + self._exp
        return raw

    def policy_check(self, event):
        raw = event.data
        if raw is None or type(raw) != type({}):
            return False
        if not "mode" in raw or raw["mode"] < 2:
            return False
        return True

