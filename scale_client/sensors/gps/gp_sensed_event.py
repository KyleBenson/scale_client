import time
from scale_client.core.sensed_event import SensedEvent

class GPSensedEvent(SensedEvent):
	def __init__(self, sensor, msg, priority,
		timestamp = None,
		gpstamp = None,
		dbtableid = None,
		upldstamp = None
	):
		SensedEvent.__init__(self, sensor, msg, priority, timestamp)
		if gpstamp is not None:
			self.gpstamp = gpstamp
		elif GPSensedEvent._gps_poller is not None:
			self.gpstamp = GPSensedEvent._gps_poller.get_dict()
		if dbtableid:
			self.dbtableid = dbtableid
			self.upldstamp = upldstamp

	def to_json(self):
		import json
		
		map_d = json.loads(SensedEvent.to_json(self))["d"]
		map_d["gpstamp"] = self.gpstamp
		return json.dumps({"d": map_d})

	_gps_poller = None

	@staticmethod
	def set_poller(_gps_poller = None):
		GPSensedEvent._gps_poller = _gps_poller

	@staticmethod
	def get_dict():
		if GPSensedEvent._gps_poller is None:
			return None
		return GPSensedEvent._gps_poller.get_dict()

	@staticmethod
	def augment(event, gpstamp = None):
		return GPSensedEvent(
			sensor = event.sensor,
			msg = event.msg,
			priority = event.priority,
			timestamp = event.timestamp,
			gpstamp = gpstamp
		)
