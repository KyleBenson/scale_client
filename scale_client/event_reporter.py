import threading
import time
from threading import Thread
from sensed_event import SensedEvent
from mqtt_publisher import MQTTPublisher
from sigfox_publisher import SigfoxPublisher

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
				# Reporter logics
				if(isinstance(pb_j, MQTTPublisher)):
					pb_j.send(event)

				#check if it is sigfox publisher
				if(isinstance(pb_j, SigfoxPublisher)):
					pb_j.send(event)
					time.sleep(1)
					pb_j.receive()
	
