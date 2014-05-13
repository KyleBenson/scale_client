import time
from random import *
from csn_virtual_sensor import CSNVirtualSensor

class DummyCSNVirtualSensor(CSNVirtualSensor):
	def __init__(self, queue, device):
		CSNVirtualSensor.__init__(self, queue, device)
		self._rand = Random()
		self._rand.seed()
		self._whatflag = True

	WAIT_MEAN = 10

	def type(self):
		return "Dummy CSN Accelerometer"

	def connect(self):
		return True

	def read(self):
		readings = []

		if self._whatflag:
			time.sleep(self._rand.random() * 2 * DummyCSNVirtualSensor.WAIT_MEAN)
			readings.append(self._rand.random() * 0.1)
			readings.append(self._rand.random() * 0.1)
			readings.append(0.0)
		else:
			readings.append(0.0)
			readings.append(0.0)
			readings.append(self._rand.random() * 0.1)

		self._whatflag = not self._whatflag
		return readings 
