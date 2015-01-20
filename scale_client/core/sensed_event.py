import time

class SensedEvent:
	def __init__(self, sensor, msg, priority, timestamp = None):
		self.sensor = sensor            # Sensor identifier
		self.msg = msg                  # A message that describes event
		self.priority = priority        # Smaller integer for higher priority
		if timestamp is None:
			self.timestamp = time.time()
		else:
			self.timestamp = timestamp

	def to_json(self):
		import json
		import copy

		map_d = copy.copy(self.msg)
	#	map_d["sensor"] = self.sensor
		map_d["timestamp"] = self.timestamp
		map_d["prio_value"] = self.priority
		if map_d["prio_value"] < 4:
			map_d["prio_class"] = "high"
		elif map_d["prio_value"] > 7:
			map_d["prio_class"] = "low"
		else:
			map_d["prio_class"] = "medium"
		return json.dumps({"d": map_d})
