from threading import Thread
from Queue import Queue

class Publisher(Thread):
	def __init__(self, name, queue_size, reporter_callback):
		Thread.__init__(self)
		self._queue_size = queue_size
		self._queue = Queue(queue_size) 
		self._callback = reporter_callback
		self._name = name

	def get_name(self):
		return self._name

	def connect(self):
		raise NotImplementedError()

	def send(self, event):
		self._queue.put(event)

	def check_available(self,event):
		raise NotImplementedError()

	def encode_event(self, event):
		raise NotImplementedError()

	def run(self):
		while True:
			event = self._queue.get()
			ret = self.publish(self.encode_event(event))
			if ret == False:
				self._callback(self, event, ret)

