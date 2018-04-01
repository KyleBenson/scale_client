from scale_client.applications.event_storing_application import EventStoringApplication

import logging
log = logging.getLogger(__name__)

import json


class EventFileLoggingApplication(EventStoringApplication):
    """
    This Application outputs all of its received events that it subscribed to into a JSON file when it stops.
    Mainly intended for testing.
    WARNING: if you let this Application run for a very long time, you'll end up with a huge list of sunk events that may
    cause memory problems
    """

    def __init__(self, broker, output_file=None, **kwargs):
        super(EventFileLoggingApplication, self).__init__(broker, **kwargs)

        if output_file:
            self.output_file = output_file
        else:
            self.output_file = "events_%s.json" % self.name

    def on_stop(self):
        """Records the received picks for consumption by another script
        that will analyze the resulting performance."""

        with open(self.output_file, "w") as f:
            log.debug("outputting sunk events to file %s" % self.output_file)
            f.write(json.dumps([e.to_map() for e in self.events], indent=2))

        super(EventFileLoggingApplication, self).on_stop()
