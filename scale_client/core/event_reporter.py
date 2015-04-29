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
        log.debug("received event type: " + et)

        if et == "location_manager_ack":
            self._lman = ed
            log.debug("received location manager")
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
