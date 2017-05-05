from event_sink import EventSink

import logging
log = logging.getLogger(__name__)
# go ahead and set the logger to INFO here so that we always log the events in question
log.setLevel(logging.INFO)


class LogEventSink(EventSink):
    """
    This EventSink simply prints all sunk SensedEvents to log.info
    """

    def send_raw(self, encoded_event):
        msg = "event sunk: %s" % encoded_event
        log.info(msg)
