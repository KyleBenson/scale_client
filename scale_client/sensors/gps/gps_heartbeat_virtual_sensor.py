import time
from scale_client.sensors.heartbeat_virtual_sensor import HeartbeatVirtualSensor
from scale_client.sensors.gps.gp_sensed_event import GPSensedEvent

class GPSHeartbeatVirtualSensor(HeartbeatVirtualSensor):
	def __init__(self, queue, device, interval):
		HeartbeatVirtualSensor.__init__(self, queue, device, interval)

	def get_type(self):
		return "gps_heartbeat"

	def policy_check(self, data):
		ls_event = HeartbeatVirtualSensor.policy_check(self, data)
		gpstamp = GPSensedEvent.get_dict()
		for j in range(0, len(ls_event)):
			ls_event[j] = GPSensedEvent.augment(ls_event[j], gpstamp)
		return ls_event
