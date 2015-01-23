import threading
import time
from threading import Thread
from sensed_event import SensedEvent
import sys

class EventReporter(Thread):
	def __init__(self, queue):
		Thread.__init__(self)
		self._queue = queue
		self._ls_pb = []
		self._ls_queue = []
		self._dict_pb = {}

	def append_publisher(self, pb):
		pb_name = pb.get_name()
		if pb_name in self._dict_pb:
			print >>sys.stderr, "Publisher name %s is already taken." % pb_name
		self._ls_pb.append(pb)
		self._dict_pb[pb_name] = pb

	def send_callback(self, pb, event, result, reason = None):
		# print pb.get_name() + " returns " + str(result)
		if pb.get_name() == "MQTT":
			if hasattr(event, "dbtableid"):
				if "MySQL" in self._dict_pb:
					if result == True:
						self._dict_pb["MySQL"].update_upldstamp(
							event.dbtableid,
							time.time()
						)
					elif result == False:
						self._dict_pb["MySQL"].update_upldstamp(
							event.dbtableid,
							None
						)

		return True 

	def run(self):
		while True:
			event = self._queue.get()
			"""
			for pb_j in self._ls_pb:
				if pb_j.check_available(event)==True:
					pb_j.send(event)
			"""

			pb_j = None
			if hasattr(event, "gpstamp") and not hasattr(event, "dbtableid"):
				if "MySQL" in self._dict_pb:
					pb_j = self._dict_pb["MySQL"]
			else:
				if "MQTT" in self._dict_pb:
					pb_j = self._dict_pb["MQTT"]
			if pb_j is not None:
				pb_j.send(event)
