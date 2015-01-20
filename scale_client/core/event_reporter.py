import threading
import time
from threading import Thread
from sensed_event import SensedEvent

class EventReporter(Thread):
	def __init__(self, queue):
		Thread.__init__(self)
		self._queue = queue
		self._ls_pb = []
		self._ls_queue = []

	def append_publisher(self, pb):
		self._ls_pb.append(pb)

	def send_false_callback(self, pb, event, false_reason):
		#TODO: Need to have a send fail dealing policy, Now we just discard
		print pb.get_name()+" send failed" 
		return True 

	def run(self):
		while True:
			event = self._queue.get()

			for pb_j in self._ls_pb:
				if pb_j.check_available(event)==True:
					pb_j.send(event)
