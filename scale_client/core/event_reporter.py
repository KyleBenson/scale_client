from application import Application 

import time
import logging
log = logging.getLogger(__name__)

class EventReporter(Application):
    """
    The EventReporter is a special-purpose Application that is the sole entity responsible
    for managing how SensedEvents are transferred to other locations in the network.  It
    does not directly call on network devices, sockets, etc. to transfer this data.
    Rather, it decides which SensedEvents to report when and then chooses from the
    available Publishers the ideal one to report the data via.
    """
    def __init__(self, broker):
        super(EventReporter, self).__init__(broker)
        self.__sinks = []
        self._lman = None
        self._neta = None

    def add_sink(self, sink):
        """
        Registers the given EventSink with the EventReporter.
        Note that the order in which you add them matters as we
        currently have no other way of distinguishing the priority 
        in which the EventReporter should consider each
        EventSink (currently it tries the first added one, then second...)
        :param sink:
        """
        self.__sinks.append(sink)

    #TODO: remove_sink?

    def on_event(self, event, topic):
        """
        Every time any SensedEvent is published, 
        we should determine whether to report it or not and then do so.
        """
        et = event.get_type()
        ed = event.get_raw_data()
        log.debug("received event type: " + et)

        if et == "location_manager_ack":
            self._lman = ed
            log.debug("received location manager")
            return

        if et == "internet_access":
            self._neta = ed
            if ed is not None:
            	if ed:
            		log.info("Internet access successful")
            	else:
            		log.info("Internet access failed")
            else:
            	log.info("Internet access status unknown")
            return

        # Ignorance
        if self._lman is not None:
            if et in self._lman.SOURCE_SUPPORT:
                return
            if et != "location_update":
                self._lman.tag_event(event)

        # Send event to sinks
        for sink in self.__sinks:
            if sink.check_available(event):
                sink.send_event(event)
                # TODO: only send via one of the sinks?

"""
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

			pb_j = None
			if hasattr(event, "gpstamp") and not hasattr(event, "dbtableid"):
				if "MySQL" in self._dict_pb:
					pb_j = self._dict_pb["MySQL"]
			else:
				if "MQTT" in self._dict_pb:
					pb_j = self._dict_pb["MQTT"]
			if pb_j is not None:
				pb_j.send(event)
"""
