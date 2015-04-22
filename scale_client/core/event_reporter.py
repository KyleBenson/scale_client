from application import Application 

import time

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

        # Location info maintenance
        self._location = None

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
        ed = event.data["value"] #ed = event.get_raw_data()

        # Ignorance
        if et == "geo_ip":
            return

        # Location info maintenance XXX: Looks thread-unsafe
        if et == "location_update":
            if not "lat" in ed or not "lon" in ed:
                raise ValueError # This should not happen
            self._location = ed
        elif self._location is not None:
            if self._location["expire"] < time.time():
                sefl._location = None
                #TODO: What else can we do? Request a location update?

        #TODO: Tag the event
        if self._location is None:
            pass
        elif type(self._location) == type({}):
            event.data["geotag"] = {"lon": self._location["lon"],
                                    "lat": self._location["lat"]}
        else: raise ValueError

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
