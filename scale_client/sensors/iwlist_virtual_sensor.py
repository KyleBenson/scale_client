import time
import iwlib
from iwlib import iwlist
from scale_client.core.sensed_event import SensedEvent
from scale_client.sensors.virtual_sensor import VirtualSensor

class IWListVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval = 4, if_name = None):
		super(IWListVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._interval = interval
		self._if_name = if_name

	def get_type(self):
		return "iwlist_scan"

	def connect(self, if_name = None):
		if if_name:
			self._if_name = if_name
		try:
			iwlist.scan(self._if_name)
		except TypeError as err:
			print err
			return False
		except OSError as err:
			print err
			return False
		return True

	def read(self):
		time.sleep(self._interval)
		return iwlist.scan(self._if_name)

	def policy_check(self, data):
		ls_ap = data
		ls_event = []
		timestamp = time.time()

		for ap in ls_ap:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(),
						"value": ap,
						"condition": {}
					},
					priority = 9,
					timestamp = timestamp
				)
			)
		return ls_event
