import time
from virtual_sensor import VirtualSensor
from sensed_event import SensedEvent

class HeartbeatVirtualSensor(VirtualSensor):
	def __init__(self, queue, device, interval):
		VirtualSensor.__init__(self, queue, device)
		self._interval = interval

	def type(self):
		return "Heartbeat Generator"

	def connect(self):
		return True

	def read(self):
		time.sleep(self._interval)
		return True

	def policy_check(self, data):
		ls_event = []
		if data == True:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": "alive",
					},
					priority = 700
				)
			)
		return ls_event
