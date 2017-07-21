from scale_client.core.application import Application
import logging
log = logging.getLogger(__name__)


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
        :param topic: the Topic the Event was published to
        """
        if topic is None:
            topic = event.get_type()

        if not event.data.has_key('touched_by_test_app'):
            log.debug("TestApp received event (topic %s): %s" % (topic, event))

        raw_data = event.get_raw_data()
        try:
            event.set_raw_data(raw_data + self.increment)
        except (ValueError, TypeError):
            # maybe not be a numeric value?
            try:
                event.set_raw_data(float(raw_data) + self.increment)
            except ValueError:
                # can't even parse a numeric, so hopefully a string?
                if isinstance(raw_data, str):
                    event.set_raw_data(raw_data + str(self.increment))
                else:
                    event.set_raw_data(self.increment)
                    event.set_type("TEST_EVENT")

        # TODO: perhaps the topic should be different to avoid loops?  For now, we just
        # XXX: hack to avoid infinite looping with this event
        if not event.data.has_key('touched_by_test_app'):
            event.data['touched_by_test_app'] = True
            self.publish(event, topic)
