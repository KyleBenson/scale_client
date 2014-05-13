import time
from random import *
from light_virtual_sensor import LightVirtualSensor

class DummyLightVirtualSensor(LightVirtualSensor):
	def __init__(self, queue, device, threshold):
		LightVirtualSensor.__init__(self, queue, device, None, threshold)
		self._rand = Random()
		self._rand.seed()
		self._darkflag = True
	
	DRK_MEAN = 20
	BRT_MEAN = 1000

	def type(self):
		return "Dummy Light Sensor"

	def connect(self):
		return True

	def read(self):
		time.sleep(1)
		if self._rand.random() < 0.05:
			self._darkflag = not self._darkflag
		if self._darkflag:
			return DummyLightVirtualSensor.DRK_MEAN
		else:
			return DummyLightVirtualSensor.BRT_MEAN
