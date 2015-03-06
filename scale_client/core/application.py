from threading import Thread
import logging
logging.basicConfig()
log = logging.getLogger(__name__)

# TODO: make this the abstract base version and do an implementation
# TODO: have smart choosing of implementations where multiple classes are implemented in this module and
# the one true "Application" implementation is exported as whichever the best of those is that can be imported
# (or that is specified in config??).  It seems that handling this exporting in core/__init__.py will lead to issues
# when another class, e.g. event_reporter, wants to import Application as relative imports apparently cannot be used
# in a non-package
class Application(Thread):
    """
    Applications may subscribe to events and may respond to them
    (or some internal logic) by publishing events.
    These are the core of the system and any classes adding additional
    functionality should at least indirectly subclass Application.

    QUESTIONS:
    1) should all events be routed through an on_event(event, topic) function where the developer must add logic
    for appropriately routing the event to other handlers
    --OR--
    should the appropriate handler function be specified in the subscribe(topic, handler) function??

    2) Should the actions taken in the run() loop be modifiable by the developer,
    or should we possibly add in some callbacks that can be called within that loop?  It seems that no we shouldn't the
       run() function is a black box that handles the asynchronous runtime and any logic for periodically reading values
       or polling for something should be handled by asynchronous callbacks tied to timers.  Should there then be some
       fire_every(time, callback) function for Applications to easily abstract the actual mechanism with which these
       timers are created?

         For example, how would the ZigBeeVirtualSensor read packets?  Does it need to keep polling
       or should we assume there's always a way of setting up a callback to do so?  What if we just specify an innermost
       function that is executed by the run() loop constantly and it normally just sleeps indefinitely but a developer
       can override it to do something slightly different (sleep 10ms then read from blahblah)?

    3) How to support historical queries of events?  This will certainly be something that VirtualSensors should support
    and likely some applications will want to do so as well so this should probably be built into this most basic of
    core classes....  Perhaps this should be handled by exposing some API at the broker rather than building this logic
    into the Application, which would require one API here and yet another (albeit more internal) API at the broker for
    actually handling the true low-level logic.

    In the future, they will support migrating between processes,
    both between those on local and remote machines.
    """

    def __init__(self, broker):
        super(Application, self).__init__(self)
        self._broker = broker

    # TODO: get_name()?

    def on_event(self, event, topic):
        """
        This callback is where you should handle the Application's logic for responding to events to which it has
        subsribed.
        :param event: the Event just published
        :param topic: the Topic the Event was published to
        """

    def on_setup(self):
        """
        This callback is fired as soon as the Application is started.  Use it to handle any setup such as network
        connections, constructing classes, or subscribing to event Topics.
        """
        pass

    def on_teardown(self):
        """
        This callback is fired when an Application is shut down (including when the whole system is doing so).  Use it
        to free any resources, close network connections, save state, etc.
        """
        pass

    def on_publish(self, event, topic):
        """
        Callback fired after successfully publishing an event
        :param event: the Event published
        :param topic: Topic the Event was published to
        :return: ignored
        """
        pass

    def on_subscribe(self, topic):
        """
        Callback fired after successfully subscribing to a Topic
        :param topic: Topic the Event was published to
        :return: ignored
        """
        pass

    def publish(self, event, topic):
        """
        Publishes the given Event to the given Topic
        :param event: Event to publish
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        raise NotImplementedError()
        self.on_publish(event, topic)
        return True

    def subscribe(self, topic):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to this
        Application via the on_event() callback.
        :param topic: the Topic to subscribe to
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

    def run(self):
        """
        This should always be called to start the Application.  You should expect, but not rely on, implementations of
        Application to make this function asynchronous, that is it will likely return immediately and do the actual
        starting up in the background.
        :return: a True-ish object if successful
        """
        raise NotImplementedError()

        while True:
            data = self.read()
            self.report_event(self.policy_check(data))
