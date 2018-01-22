from event_sink import EventSink
from scale_client.applications.event_file_logging_application import EventFileLoggingApplication

import logging
log = logging.getLogger(__name__)


class FileEventSink(EventFileLoggingApplication, EventSink):
    """
    This EventSink simply outputs all of its sunk events into a JSON file when it stops.  Mainly intended for testing.
    WARNING: if you let this EventSink run for a very long time, you'll end up with a huge list of sunk events that may
    cause memory problems
    """

    def send_event(self, event):
        # no need to encode the event at this point since we're just storing it in a queue
        EventFileLoggingApplication.on_event(self, event)