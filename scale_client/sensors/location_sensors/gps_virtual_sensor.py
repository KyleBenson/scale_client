from scale_client.sensors.virtual_sensor import VirtualSensor
from gps_poller import GPSPoller

import json
import time
import logging
log = logging.getLogger(__name__)

class GPSVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=1, exp=10, **kwargs):
		super(GPSVirtualSensor, self).__init__(broker, device=device, interval=interval, **kwargs)
		self._exp = exp
		self._gps_poller = None

	def on_start(self):
		self._gps_poller = GPSPoller()
		self._gps_poller.daemon = True
		self._gps_poller.start()
		super(GPSVirtualSensor, self).on_start()

	def get_type(self):
		return "gps"

	def read_raw(self):
		if self._gps_poller is None:
			return None
		raw = self._gps_poller.get_dict()
		if type(raw) != type({}):
			return None
		raw["exp"] = time.time() + self._exp
		return raw
	
	def read(self):
		raw = self.read_raw()
		event = self.make_event_with_raw_data(raw, priority=7)
		return event

	def policy_check(self, data):
		raw = data.get_raw_data()
		if raw is None or type(raw) != type({}):
			return False
		if not "mode" in raw or raw["mode"] < 2:
			return False
		return True

