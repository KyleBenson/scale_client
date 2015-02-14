from __future__ import print_function
import subprocess
import re

from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.sensed_event import SensedEvent


class TemperatureVirtualSensor(VirtualSensor):
	def __init__(
		self, queue, device,
		daemon_path,
		threshold
	):
		VirtualSensor.__init__(self, queue, device)
		self._daemon_path = daemon_path
		self._threshold = threshold
		self._result = None
		self._regexp = re.compile(r'Device ([^:]*): Sensor ([0-9]*): Temperature: ([0-9\.]*)')

	def get_type(self):
	#	return "Temperature Sensor"
	#	return "SCALE_Temp_Sheeva"
		return "temperature"

	def connect(self):
		self._result = subprocess.Popen(
		#	['temperature-streams'],
			[self._daemon_path],
			shell=True,
			stdout=subprocess.PIPE
		)
		return True

	def read(self):
		line = next(iter(self._result.stdout.readline, '')) 
		match = self._regexp.match(line)
		try:
			temperature = float(match.group(3))
		except AttributeError as e:
			print('Error parsing temperature: %s' % e)
		return temperature

	def policy_check(self, data):
		ls_event = []
		if data > self._threshold:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(), #"SCALE_high_heat_Sheeva",
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
		"""	if True:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(), #"SCALE_raw_Temp_Sheeva",
						"value": data,
						"condition": {}
					},
					priority = 10
				)
			)"""
		return ls_event
