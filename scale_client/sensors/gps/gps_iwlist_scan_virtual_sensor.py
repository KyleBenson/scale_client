import time
from scale_client.sensors.iwlist_scan_virtual_sensor import IWListScanVirtualSensor
from scale_client.sensors.gps.gp_sensed_event import GPSensedEvent

class GPSIWListScanVirtualSensor(IWListScanVirtualSensor):
	def __init__(self, interval = 10, **kwargs):
		IWListScanVirtualSensor.__init__(self, interval = interval, **kwargs)

	def get_type(self):
		return "gps_iwlist_scan"

	def policy_check(self, data):
		gpstamp = GPSensedEvent.get_dict()
		if gpstamp is None or gpstamp["mode"] < 2:
			return []

		ls_event = IWListScanVirtualSensor.policy_check(self, data)
		for j in range(0, len(ls_event)):
			ls_event[j] = GPSensedEvent.augment(ls_event[j], gpstamp)
		return ls_event
