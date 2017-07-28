from scale_client.sensors.virtual_sensor import VirtualSensor

import time
import copy
import logging
log = logging.getLogger(__name__)

class FakeLocationVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=60, exp=600, lat=0.0, lon=0.0, alt=None, **kwargs):
		super(FakeLocationVirtualSensor, self).__init__(broker, device=device, interval=interval, **kwargs)
		self._exp = exp
		self._tag = {}
		if type(lat) != type(0.0) or type(lon) != type(0.0):
			raise TypeError
		self._tag["lat"] = lat
		self._tag["lon"] = lon
		if alt is not None:
			if type(alt) != type(0.0):
				raise TypeError
			self._tag["alt"] = alt

	DEFAULT_PRIORITY = 3

	def get_type(self):
		return "fake_location"

	def read_raw(self):
		raw = copy.copy(self._tag)
		raw["exp"] = time.time() + self._exp
		return raw

	def policy_check(self, data):
		return True
