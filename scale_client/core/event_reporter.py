from application import Application 
from sensed_event import SensedEvent

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
        self._mysql_sink = None
        self._puba = None

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

        elif et == "publisher_state":
            return

        # Ignorance <--- what does this mean???
        if self._lman is not None:
            if et in self._lman.SOURCE_SUPPORT:
                return
            if et != "location_update":
                self._lman.tag_event(event)

        # Send event to sinks
        published = False
        for sink in self.__sinks:
            if type(sink).__name__ == "MySQLEventSink":
                if self._mysql_sink is None:
                    self._mysql_sink = sink
                try:
                    self.__sinks.remove(sink)
                    log.info("found MySQL database connector")
                except ValueError:
                    pass
            elif sink.check_available(event):
                if sink.send_event(event):
                    published = True
                # TODO: only send via one of the sinks?

        # Update publisher state
        if published:
            self._cast_publisher_state(published, 8)
        if hasattr(event, "db_record"): # from database
            if published: # update database record
                event.db_record["upload_time"] = time.time()
            else:
                # Update publisher state
                self._cast_publisher_state(published, 7)
        else: # not from database
            if published: # no need to insert into database
                return
        if self._mysql_sink is not None:
            if self._mysql_sink.check_available(event):
                self._mysql_sink.send_event(event)
    
    def _cast_publisher_state(self, published, priority):
        if self._puba is not None and self._puba == published:
            return
        self._puba = published
        ps = SensedEvent(
                sensor="event_reporter",
                data={"event": "publisher_state", "value": published},
                priority=priority
            )
        self.publish(ps)

