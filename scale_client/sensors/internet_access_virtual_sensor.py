from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

from urllib2 import urlopen
from time import time as get_time
import logging
log = logging.getLogger(__name__)

class InternetAccessVirtualSensor(ThreadedVirtualSensor):
	def __init__(self, broker, device=None, interval=5, lookup_url="http://www.google.com", timeout=2, timer_threshold=60):
		super(InternetAccessVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._lookup_url = lookup_url
		self._timeout = timeout
		self._last_value = None
		self._timer = get_time()
		self._timer_threshold = timer_threshold

	def get_type(self):
		return "internet_access"

	def read_raw(self):
		try:
			urlopen(self._lookup_url, timeout=self._timeout)
		except Exception:
			return False
		return True
	
	def read(self):
		raw = self.read_raw()
		event = self.make_event_with_raw_data(raw, priority=8)
		return event

	def policy_check(self, data):
		raw = data.get_raw_data()
		success = False
		if raw != self._last_value or self._timer + self._timer_threshold > get_time():
			self._timer = get_time()
			success = True
		self._last_value = raw
		return success
