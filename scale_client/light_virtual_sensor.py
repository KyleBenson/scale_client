
from __future__ import print_function
import subprocess
import re
from analog_virtual_sensor import AnalogVirtualSensor
from sensed_event import SensedEvent
import time


class LightVirtualSensor(AnalogVirtualSensor):
	def __init__(self, queue, device, analog_port, threshold):
		AnalogVirtualSensor.__init__(self, queue, device, analog_port)
		self._threshold = threshold

	def type(self):
		return "Light Sensor"

	def read(self):
		time.sleep(1)
                raw_reading = self._spi.xfer2([1,8+self._port <<4,0])
                adcout = ((raw_reading[1] &3) <<8)+raw_reading[2]
                return adcout

	def policy_check(self, data):
		if data < self._threshold:
			return True
		else:
			return False

	def report_event(self, data):
		self._queue.put(
			SensedEvent(
				sensor = self.device.device,
				msg = "Dark Enviroment",
				priority = 50
			)
		)
