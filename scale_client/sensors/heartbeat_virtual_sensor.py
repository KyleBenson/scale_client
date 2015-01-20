import time

from scale_client.sensors.virtual_sensor import VirtualSensor
from sensed_event import SensedEvent


class HeartbeatVirtualSensor(VirtualSensor):
	def __init__(self, queue, device, interval):
		VirtualSensor.__init__(self, queue, device)
		self._interval = interval

	def get_type(self):
	#	return "Heartbeat Generator"
	#	return "SCALE_Heartbeat"
		return "heartbeat"

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
						"event": self.get_type(), #"SCALE_alive",
						"value": None,
						"condition": {}
					},
					priority = 10
				)
			)
		return ls_event
