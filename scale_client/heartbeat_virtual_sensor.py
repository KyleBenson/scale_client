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
		pass

	def read(self):
		time.sleep(self._interval)
		return True

	def policy_check(self, data):
		if data == True:
			return True

	def report_event(self, data):
		if data == True:
			self._queue.put(
				SensedEvent(
					sensor = self.device.device,
					msg = "I am running",
					priority = 700
				)
			)