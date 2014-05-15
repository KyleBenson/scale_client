import threading
import time
from threading import Thread
from sensed_event import SensedEvent

class EventReporter(Thread):
	def __init__(self, queue):
		Thread.__init__(self)
		self._queue = queue
		self._ls_pb = []

	def append_publisher(self, pb):
		self._ls_pb.append(pb)

	def run(self):
		while True:
			event = self._queue.get()

			for pb_j in self._ls_pb:
				pb_j.send(event)
