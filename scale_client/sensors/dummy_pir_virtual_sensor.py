import time
from random import *

from scale_client.sensors.pir_virtual_sensor import PIRVirtualSensor


class DummyPIRVirtualSensor(PIRVirtualSensor):
	def __init__(self, broker, device):
		PIRVirtualSensor.__init__(self, broker, device, None)
		self._rand = Random()
		self._rand.seed()
		self._darkflag = True
	
	IDLE = 0
	ACTIVE = 1
	
	def connect(self):
		return True

	def read(self):
		time.sleep(0.001)
		if self._rand.random() < 0.001:
			self._darkflag = not self._darkflag
		if self._darkflag:
			return 0
		else:
			return 1
