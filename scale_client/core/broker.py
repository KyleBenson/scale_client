from threading import Thread

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


#TODO: abstract base class??  same with App?
class Broker(Thread):
    """
    This purely abstract base class represents the API for the local publish-subscribe broker than handles routing and
    delivery of generic Events in the whole system.  It works as a singleton object that, when instantiated, will fire
    any registered callbacks upon publication of a new Event.

    QUESTIONS:
    1) Should the Broker also be responsible for handling duplicate Events through perhaps assigning sequence numbers
    or a logical clock?
    2) How long do SensedEvents stick around for?
    """

    def __init__(self):
        super(Broker, self).__init__(self)

    def publish(self, event, topic):
        """
        Publishes the given SensedEvent to the given Topic
        :param event: Event to publish
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        raise NotImplementedError()
        self.on_publish(event, topic)
        return True

    def subscribe(self, topic, callback):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to
        the specified callback.
        :param topic: the Topic to subscribe to
        :param callback: the Callback to call with the newly published Event as the argument
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

    def run(self):
        """
        This should always be called to start the Application.  You should expect, but not rely on, implementations of
        Broker to make this function asynchronous, that is it will likely return immediately and do the actual
        starting up in the background.
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

        while True:
            data = self.read()
            self.report_event(self.policy_check(data))
