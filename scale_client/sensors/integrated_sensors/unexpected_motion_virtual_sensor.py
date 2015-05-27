from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.sensors.pir_virtual_sensor import PIRVirtualSensor
from scale_client.sensors.light_virtual_sensor import LightVirtualSensor

from time import time as get_time
import logging
log = logging.getLogger(__name__)


class UnexpectedMotionVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, inact_threshold=600, darktime=60):
		super(UnexpectedMotionVirtualSensor, self).__init__(broker=broker, device=device, interval=None)
		self._light = LightVirtualSensor.DARK
		self._dark_timer = get_time()
		self._dark_timeout = darktime

	DEFAULT_PRIORITY = 5

	def get_type(self):
		return "unexpected_motion"
	
	def on_event(self, event, topic):
		et = event.get_type()
		ed = event.get_raw_data()

		if et == "motion":
			if ed == PIRVirtualSensor.ACTIVE and self._light == LightVirtualSensor.DARK:
				if type(self._dark_timer) != type(9.0):
					log.warning("Timer is not set correctly")
				elif self._dark_timer + self._dark_timeout < get_time():
					new_event = self.make_event_with_raw_data(ed, priority=self.DEFAULT_PRIORITY)
					self.publish(new_event)
		elif et == "light":
			op = None
			try:
				op = event.data["condition"]["threshold"]["operator"]
			except (KeyError, AttributeError):
				pass
			if op == ">":
				self._light = LightVirtualSensor.BRIGHT
				self._dark_timer = None
			elif op == "<":
				self._light = LightVirtualSensor.DARK
				self._dark_timer = get_time()
			else:
				log.warning("Unsupported structure in light event")

	def policy_check(self, event):
		return False
