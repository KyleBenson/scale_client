from time import sleep
from virtual_sensor import VirtualSensor
from ..core.threaded_application import ThreadedApplication

import logging
log = logging.getLogger(__name__)

class ThreadedVirtualSensor(VirtualSensor, ThreadedApplication):
	"""
	Does its sensor reading in a background loop instead of using
	the repeat feature of Application.timed_call()
	"""
	def __init__(self, broker, device=None, interval=1, process=False, n_threads=1):
		VirtualSensor.__init__(self, broker, device=device, interval=interval)
		ThreadedApplication.__init__(self, broker, process=process, n_threads=n_threads)

	def sensor_loop(self, interval):
		while True:
			self._do_sensor_read()
			sleep(interval)

	def on_start(self):
		self.run_in_background(self.sensor_loop, self._wait_period)