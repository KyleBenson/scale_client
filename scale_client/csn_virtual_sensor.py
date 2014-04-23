import threading
from threading import Thread
from virtual_csn_server.main import *
from Queue import Queue
from virtual_sensor import VirtualSensor

_raw_event_queue = Queue()

class CsnVirtualSensor(VirtualSensor):
	def __init__(self, queue, device):
		VirtualSensor.__init__(self, queue, device)

	def type(self):
		return "CSN Accelerometer"

	def connect(self):
		#TODO: fix this name....
		main()

	def read(self):
		return _raw_event_queue.get()

	def policy_check(self, data):
		return True

	def report_event(self, data):
		print data
		event = SensedEvent(self.device.device, "Pick detected", 70)
		self._queue.put(event)

	def run(self):
		while True:
			data = self.read()
			if self.policy_check(data):
				self.report_event(data)
