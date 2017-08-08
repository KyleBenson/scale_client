import logging
from time import time as get_time

from scale_client.sensors.environment.light_physical_sensor import LightPhysicalSensor

from scale_client.sensors.environment.pir_physical_sensor import PirPhysicalSensor
from scale_client.sensors.virtual_sensor import VirtualSensor

log = logging.getLogger(__name__)


class UnexpectedMotionVirtualSensor(VirtualSensor):
	def __init__(self, broker, darktime=60, event_type="unexpected_motion", **kwargs):
		super(UnexpectedMotionVirtualSensor, self).__init__(broker=broker, subscriptions=("motion",),
                                                            sample_interval=None, event_type=event_type, **kwargs)
		self._light = LightPhysicalSensor.DARK
		self._dark_timer = get_time()
		self._dark_timeout = darktime

	DEFAULT_PRIORITY = 5
	
	def on_event(self, event, topic):
		et = event.event_type
		ed = event.data

		if et == "motion":
			if ed == PirPhysicalSensor.ACTIVE and self._light == LightPhysicalSensor.DARK:
				if type(self._dark_timer) != type(9.0):
					log.warning("Timer is not set correctly")
				elif self._dark_timer + self._dark_timeout < get_time():
					new_event = self.make_event(data=ed)
					self.publish(new_event)
		elif et == "light":
			op = None
			try:
				op = event.condition["threshold"]["operator"]
			except (KeyError, AttributeError):
				pass
			if op == ">":
				self._light = LightPhysicalSensor.BRIGHT
				self._dark_timer = None
			elif op == "<":
				self._light = LightPhysicalSensor.DARK
				self._dark_timer = get_time()
			else:
				log.warning("Unsupported structure in light event")

	# we always publish since we're doing it explicitly
	def policy_check(self, event):
		return False
