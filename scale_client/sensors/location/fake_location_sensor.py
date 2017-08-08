from scale_client.sensors.virtual_sensor import VirtualSensor

import time
import copy
import logging
log = logging.getLogger(__name__)

class FakeLocationSensor(VirtualSensor):
	def __init__(self, broker, exp=600, lat=0.0, lon=0.0, alt=None, event_type="fake_location", **kwargs):
		super(FakeLocationSensor, self).__init__(broker, event_type=event_type, **kwargs)
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

	def read_raw(self):
		raw = copy.copy(self._tag)
		raw["exp"] = time.time() + self._exp
		return raw

	def policy_check(self, data):
		return True
