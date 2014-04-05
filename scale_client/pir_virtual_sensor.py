
from __future__ import print_function
import subprocess
import re
from gpio_virtual_sensor import GPIOVirtualSensor
from sensed_event import SensedEvent
import RPi.GPIO as GPIO


class PIRVirtualSensor(GPIOVirtualSensor):
	def __init__(self, queue, device, gpio_pin):
		GPIOVirtualSensor.__init__(self, queue, device, gpio_pin)
		self._state = PIRVirtualSensor.IDLE 

	IDLE = 0
	ACTIVE = 1

	def type(self):
		return "PIR Motion Sensor"

	def read(self):
		input_value = self._GPIO.input(self._pin)
		return input_value

	def policy_check(self, data):
		if self._state == PIRVirtualSensor.IDLE:
	                if data == 0:
        	                return False
              		if data == 1:
                       		self._state = PIRVirtualSensor.ACTIVE
                       		return True

        	if self._state == PIRVirtualSensor.ACTIVE:
                	if data == 0:
                        	self._state = PIRVirtualSensor.IDLE
                        	return False
                	if data == 1:
                        	return False


	def report_event(self, data):
		self._queue.put(
			SensedEvent(
				sensor = self.device.device,
				msg = "Movement Detected",
				priority = 50
			)
		)
