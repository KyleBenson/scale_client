from threading import Thread
from Queue import Queue


class Publisher(Thread):
    """Publishers handle forwarding SensedEvents to some end-point possibly via a particular network interface."""

    def __init__(self, name=None, queue_size=100, reporter_callback=None):
        Thread.__init__(self)
        self._queue_size = queue_size
        self._queue = Queue(queue_size)
        #TODO: is having pubs refers to reporter okay??? sounds circular...
        self._callback = reporter_callback
        self._name = name

    def get_name(self):
        return self._name

    def connect(self):
        """Derived publishers should not add any args to the connect function.
          Pass all args into constructor instead."""
        raise NotImplementedError()

    def send(self, event):
        self._queue.put(event)

    def check_available(self, event):
        raise NotImplementedError()

    def encode_event(self, event):
        raise NotImplementedError()

    def run(self):
        while True:
            event = self._queue.get()
            ret = self.publish(self.encode_event(event))
            if not ret:
                self._callback(self, event, ret)

