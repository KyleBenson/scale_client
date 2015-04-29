from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.threaded_application import Worker

import logging
log = logging.getLogger(__name__)

class ThreadedVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=1, process=False, n_threads=1):
		super(ThreadedVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._worker = Worker(
			process=process,
			workers=n_threads,
			channel=self._get_channel_name()
		)
		self._worker.register(self)

	def run_in_background(self, f, *args, **kwargs):
		self.fire(task(f, *args, **kwargs), self._get_channel_name())

	def on_start(self):
		self.run_in_background(VirtualSensor.on_start, self)