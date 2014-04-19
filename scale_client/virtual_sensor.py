import threading
from threading import Thread

class VirtualSensor(Thread):
	def __init__(self, queue, device):
		Thread.__init__(self)
		self._queue = queue
		self.device = device

	def type(self):
		raise NotImplementedError()

	def connect(self):
		raise NotImplementedError()

	def read(self):
		raise NotImplementedError()

	def policy_check(self, data):
		raise NotImplementedError()

	def report_event(self, data):
		raise NotImplementedError()

	def run(self):
		while True:
			data = self.read()
			if self.policy_check(data):
				self.report_event(data)