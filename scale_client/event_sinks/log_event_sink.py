from scale_client.event_sinks.event_sink import EventSink

import json
import logging
log = logging.getLogger(__name__)
# go ahead and set the logger to INFO here so that we always log the events in question
log.setLevel(logging.INFO)


class LogEventSink(EventSink):
    """
    This EventSink simply prints all sunk SensedEvents to log.info
    """

    def send(self, encoded_event):
        msg = "event sunk: %s" % encoded_event
        log.info(msg)

    def encode_event(self, event):
    	return json.dumps(event.to_map())