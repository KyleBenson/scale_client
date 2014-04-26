from __future__ import print_function
import subprocess
import re
from usb_virtual_sensor import USBVirtualSensor
from sensed_event import SensedEvent


class TemperatureVirtualSensor(USBVirtualSensor):
	def __init__(
		self, queue, device,
		daemon_path,
		threshold
	):
		USBVirtualSensor.__init__(self, queue, device)
		self._daemon_path = daemon_path
		self._threshold = threshold
		self._result = None
		self._regexp = re.compile(r'Device ([^:]*): Sensor ([0-9]*): Temperature: ([0-9\.]*)')

	def type(self):
		return "Temperature Sensor"

	def connect(self):
		self._result = subprocess.Popen(
			['temperature-streams'],
			shell=True,
			stdout=subprocess.PIPE
		)

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
					msg = "High Temperature: " + str(data),
					priority = 50
				)
			)
		return ls_event
