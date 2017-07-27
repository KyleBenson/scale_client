import logging
log = logging.getLogger(__name__)

class AbstractBroker(object):
    """
    This purely abstract (TODO!!!!) base class represents the API for the local publish-subscribe broker than handles routing and
    delivery of generic Events in the whole system.  It works as a singleton object that, when instantiated, will fire
    any registered callbacks upon publication of a new Event.

    QUESTIONS:
    1) Should the Broker also be responsible for handling duplicate Events through perhaps assigning sequence numbers
    or a logical clock?
    2) How long do SensedEvents stick around for?
    """

    def __init__(self):
        super(AbstractBroker, self).__init__()

    def publish(self, event, topic):
        """
        Publishes the given SensedEvent to the given Topic
        :param event: Event to publish
        :type event: sensed_event.SensedEvent
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

    def subscribe(self, topic, callback):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to
        the specified callback.
        :param topic: the Topic to subscribe to
        :param callback: the Callback to call with the newly published Event as the argument
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

    # TODO: unsubscribe
    # NOTE: we're going to need to pass a reference to the caller of these functions so we know WHO is (un)subscribing right?
    # OR we could just pass the callback and use that as the unique subscriber key...

    def run(self):
        """
        This should always be called to start the Application.  You should expect, but not rely on, implementations of
        Broker to make this function asynchronous, that is it will likely return immediately and do the actual
        starting up in the background.
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

# Now we make the actual implementation via circuits
from circuits.core.manager import Manager

class Broker(Manager, AbstractBroker):

    def __init__(self):
        Manager.__init__(self)
        AbstractBroker.__init__(self)

    def publish(self, event, topic):
        self.fireEvent(event, topic)

    def subscribe(self, topic, callback):
        raise NotImplementedError("Don't call CircuitsBroker.subscribe; instead directly call CircuitsApplication.subscribe!")