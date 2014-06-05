import threading
from threading import Thread

class VirtualSensor(Thread):
	def __init__(self, queue, device):
		Thread.__init__(self)
		self._queue = queue
		self.device = device

	def get_type(self):
		raise NotImplementedError()

	def connect(self):
		raise NotImplementedError()

	def read(self):
		raise NotImplementedError()

	def policy_check(self, data):
		raise NotImplementedError()

	def report_event(self, ls_event):
		for event in ls_event:
			self._queue.put(event)

	def run(self):
		while True:
			data = self.read()
			self.report_event(self.policy_check(data))
