import time
from random import *

from scale_client.sensors.temperature_virtual_sensor import TemperatureVirtualSensor


class DummyTemperatureVirtualSensor(TemperatureVirtualSensor):
	def __init__(self, broker, device, threshold):
		TemperatureVirtualSensor.__init__(self, broker, device, None, threshold)
		self._rand = Random()
		self._rand.seed()
		self._darkflag = True
		self.CEL_MEAN = threshold - 2

	def connect(self):
		return True

	def read(self):
		time.sleep(1)
		return round(self.CEL_MEAN + self._rand.random() * 6 - 3, 2)
