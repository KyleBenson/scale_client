from __future__ import print_function
import time

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class LightVirtualSensor(AnalogVirtualSensor):
	def __init__(self, broker, device, analog_port, threshold, flash_delta = 600):
		AnalogVirtualSensor.__init__(self, broker, device, analog_port)
		self._threshold = threshold
		self._state = LightVirtualSensor.DARK
		self._flash_delta = flash_delta
		self._last_data	= None

	DARK = 0
	BRIGHT = 1

	def get_type(self):
	#	return "Light Sensor"
	#	return "SCALE_Light_RPi"
		return "light"

	def read(self):
		time.sleep(1)
		raw_reading = self._spi.xfer2([1,8+self._port <<4,0])
		adcout = ((raw_reading[1] &3) <<8)+raw_reading[2]
		return adcout

	def policy_check(self, data):
		ls_event = []
		if self._state == LightVirtualSensor.DARK:
			if data < self._threshold:
				pass
			if data > self._threshold:
				self._state = LightVirtualSensor.BRIGHT
				ls_event.append(
					SensedEvent(
						sensor = self.device.device,
						msg = {
							"event": self.get_type(), #"SCALE_bright_environment_RPi",
							"value": data,
							"condition": {
								"threshold": {
									"operator": ">",
									"value": self._threshold
								}
							}
						},
						priority = 7
					)
				)		 
		if self._state == LightVirtualSensor.BRIGHT:
			if data > self._threshold:
				pass
			if data < self._threshold:
				self._state = LightVirtualSensor.DARK
				ls_event.append(
					SensedEvent(
						sensor = self.device.device,
						msg = {
							"event": self.get_type(), #"SCALE_dark_environment_RPi",
							"value": data,
							"condition": {
								"threshold": {
									"operator": "<",
									"value": self._threshold
								}
							}
						},
						priority = 7
					)
				)
				
		# Flash light detection
		if self._last_data is not None:
			if (data-self._last_data) > self._flash_delta:
				ls_event.append(
					SensedEvent(
						sensor = self.device.device,
						msg = {
							"event": self.get_type(), #"SCALE_flash_environment_RPi",
							"value": (data-self._last_data),
							"condition": {
								"delta": {
									"operator": ">",
									"value": self._flash_delta
								}
							}
						},
						priority = 7
					)
				) 	
		self._last_data = data
		return ls_event
