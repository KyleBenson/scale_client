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