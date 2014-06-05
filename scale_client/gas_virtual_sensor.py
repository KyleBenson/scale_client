
from __future__ import print_function
import subprocess
import re
from analog_virtual_sensor import AnalogVirtualSensor
from sensed_event import SensedEvent
import time


class GasVirtualSensor(AnalogVirtualSensor):
	def __init__(self, queue, device, analog_port, threshold):
		AnalogVirtualSensor.__init__(self, queue, device, analog_port)
		self._threshold = threshold

	def get_type(self):
		return "explosive_gas"

	def read(self):
		time.sleep(1)
		raw_reading = self._spi.xfer2([1,8+self._port <<4,0])
		adcout = ((raw_reading[1] &3) <<8)+raw_reading[2]
		return adcout

	def policy_check(self, data):
		ls_event = []
		if data > self._threshold:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(),
						"value": data,
						"condition": {
							"threshold": {
								"operator": ">",
								"value": self._threshold
							}
						}
					},
					priority = 5
				)
			)

		# Lines below are for testing purpose
		if True:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(),
						"value": data,
						"condition": {}
					},
					priority = 10
				)
			)
		return ls_event

