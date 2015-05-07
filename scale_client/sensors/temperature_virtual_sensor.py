from scale_client.sensors.virtual_sensor import VirtualSensor

import time
from usb.core import USBError
from temperusb import TemperHandler
import logging
log = logging.getLogger(__name__)


class TemperatureVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=1, threshold=24.0, search_interval=60):
		super(TemperatureVirtualSensor, self).__init__(broker, device, interval=interval)
		self._threshold = threshold
		self._search_interval = search_interval

		self._devs = None
		self._dev_timer = None

	DEFAULT_PRIORITY = 5

	def get_type(self):
		return "temperature"

	def on_start(self):
		self._get_devices()
		if self._wait_period is None:
			return
		self._do_sensor_read()
		self.timed_call(self._wait_period, TemperatureVirtualSensor._do_sensor_read, repeat=True)

	def _get_devices(self):
		self._devs = TemperHandler().get_devices()
		log.info("found %d device(s)" % len(self._devs))

	def read_raw(self, dev=None):
		if dev is None:
			raise NotImplementedError
		return round(dev.get_temperature(), 2)

	def read(self, dev=None):
		raw = self.read_raw(dev)
		event = self.make_event_with_raw_data(raw)
		event.data['condition'] = {
				"threshold": {
					"operator": ">",
					"value": self._threshold
				}
			}

		return event

	def policy_check(self, event):
		return event.data['value'] > self._threshold
	
	def _do_sensor_read(self):
		if len(self._devs) < 1:
			if self._dev_timer is None or self._dev_timer + self._search_interval < time.time():
				self._get_devices()
				self._dev_timer = time.time()
			return
		
		self._dev_timer = None
		log.debug("%s reading sensor data..." % self.get_type())
		for dev in self._devs:
			try:
				event = self.read(dev)
			except USBError:
				log.warning("device disconnected")
				self._get_devices()
				break
			if event is None:
				continue
			if self.policy_check(event):
				self.publish(event)
