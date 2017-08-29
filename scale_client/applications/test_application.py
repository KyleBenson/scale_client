from copy import deepcopy

from scale_client.core.application import Application
import logging
log = logging.getLogger(__name__)

# type annotations
from scale_client.core.sensed_event import SensedEvent

class TestApplication(Application):
    """
    This dummy app simply subscribes to all SensedEvents and tries to increment the 'value' contained within them
    by self.increment if possible or else appends a '.' if the value is a string.  If neither hold true, it simply
    replaces the value with self.increment.
    """

    def __init__(self, broker, increment=1, **kwargs):
        """
        :param broker: the broker used for the internal pub-sub feature core to the scale_client
        :param increment: a numeric/string value that a SensedEvent's value is incremented by before being republished
        :param kwargs: used for passing args to other constructors when doing multiple inheritance
        """
        super(TestApplication, self).__init__(broker, **kwargs)
        self.increment = increment

    def on_event(self, event, topic=None):
        """
        This callback is where you should handle the Application's logic for responding to events to which it has
        subscribed.
        :param event: the Event just published
        :type event: SensedEvent
        :param topic: the Topic the Event was published to
        """
        if topic is None:
            topic = event.topic

        # To make sure we don't loop forever (modifying this event each time), we only touch it once
        if not event.metadata.has_key('touched_by_test_app'):
            log.debug("TestApp received event (topic %s): %s" % (topic, event))

            # Now we try to transform the event's data by first treating it as a numeric...
            raw_data = event.data
            try:
                new_data = raw_data + self.increment
            except (ValueError, TypeError):
                # maybe not be a numeric value?
                try:
                    new_data = float(raw_data) + self.increment
                except ValueError:
                    # can't even parse a numeric, so hopefully a string?
                    if isinstance(raw_data, str):
                        new_data = raw_data + str(self.increment)
                    else:
                        new_data = self.increment

            # We create a new event from this one and then publish it!
            condition = {'event': event}
            event = deepcopy(event)
            event.data = new_data
            # especially important if the event is a remote one!
            event.source = self.path
            event.condition = condition
            event.metadata['touched_by_test_app'] = True
            self.publish(event, topic)
