
from __future__ import print_function
from time import time as get_time

from scale_client.sensors.gpio_virtual_sensor import GPIOVirtualSensor
from scale_client.core.sensed_event import SensedEvent

#import RPi.GPIO as GPIO


class PIRVirtualSensor(GPIOVirtualSensor):
	def __init__(self, queue, device, gpio_pin, inact_threshold = 600):
		GPIOVirtualSensor.__init__(self, queue, device, gpio_pin)
		self._state = PIRVirtualSensor.IDLE 
		self._inact_timer = get_time()
		self._inact_threshold = inact_threshold

	IDLE = 0
	ACTIVE = 1

	def get_type(self):
	#	return "PIR Motion Sensor"
	#	return "SCALE_PIR_RPi"
		return "motion"

	def read(self):
		input_value = self._GPIO.input(self._pin)
		return input_value

	def policy_check(self, data):
		ls_event = []
		
		# State transitions
		if self._state == PIRVirtualSensor.IDLE:
			if data == 0:
				pass
			if data == 1:
				self._state = PIRVirtualSensor.ACTIVE
				ls_event.append(
					SensedEvent(
						sensor = self.device.device,
						msg = {
							"event": self.get_type(), #"SCALE_motion_detected_RPi",
							"value": data,
							"condition": {}
						},
						priority = 7
					)
				)
		if self._state == PIRVirtualSensor.ACTIVE:
			if data == 0:
				self._state = PIRVirtualSensor.IDLE
				self._inact_timer = get_time()
			if data == 1:
				pass

		# State tasks				
		if self._state == PIRVirtualSensor.IDLE:
			if (get_time() - self._inact_timer) > self._inact_threshold:
				ls_event.append(
					SensedEvent(
						sensor = self.device.device,
						msg = {
							"event": self.get_type(), #"SCALE_motion_detected_RPi",
							"value": data,
							"condition": {
								"inactive_time": {
									"operator": ">",
									"value": self._inact_threshold
								}
							}
						},
						priority = 7
					)
				)
				self._inact_timer = get_time()
		return ls_event
