import time
from random import *
from gas_virtual_sensor import GasVirtualSensor

class DummyGasVirtualSensor(GasVirtualSensor):
	def __init__(self, queue, device, threshold):
		GasVirtualSensor.__init__(self, queue, device, None, threshold)
		self._rand = Random()
		self._rand.seed()
		self._darkflag = True
		self._dummyval = DummyGasVirtualSensor.DRK_MEAN
	
	DRK_MEAN = 110
	BRT_MEAN = 800

	def type(self):
		return "Dummy Gas Sensor"

	def connect(self):
		return True

	def read(self):
		time.sleep(1)
		if self._rand.random() < 0.05:
			self._darkflag = not self._darkflag
		if self._darkflag:
			self._dummyval = int(self._dummyval * 0.5 + DummyGasVirtualSensor.DRK_MEAN * 0.5)
		else:
			self._dummyval = DummyGasVirtualSensor.BRT_MEAN
			self._darkflag = not self._darkflag
		return self._dummyval
