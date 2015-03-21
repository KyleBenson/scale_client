import circuits
# note that we'll always keep around a 'handler' decorator even if we stop using circuits!
from circuits.core.handlers import handler
from scale_client.core.sensed_event import SensedEvent

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


# TODO: have smart choosing of implementations where multiple classes are implemented in this module and
# the one true "Application" implementation is exported as whichever the best of those is that can be imported
# (or that is specified in config??).  It seems that handling this exporting in core/__init__.py will lead to issues
# when another class, e.g. event_reporter, wants to import Application as relative imports apparently cannot be used
# in a non-package

# TODO: make this the abstract base version and do an implementation
#class AbstractApplication(object):
class Application(circuits.BaseComponent):
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

    def __init__(self, broker=None):
        super(Application, self).__init__(self)
        if broker is None:
            raise NotImplementedError
        self._register_broker(broker)

    # TODO: get_name()?

    def _register_broker(self, broker):
        """Connects this Application to the specified pub-sub event broker.  This method is automatically called for
        you and should really only be used for testing purposes.

        The circuits implementation registers the Component to the Broker"""
        self._broker = broker
        self.register(broker)

    def on_event(self, event, topic):
        """
        This callback is where you should handle the Application's logic for responding to events to which it has
        subscribed.
        :param event: the Event just published
        :param topic: the Topic the Event was published to
        """
        pass

    def on_start(self):
        """
        This callback is fired as soon as the Application is started.  Use it to handle any setup such as network
        connections, constructing classes, or subscribing to event Topics.
        """
        pass

    def on_stop(self):
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

    #TODO: unsubscribe?

    def publish(self, event, topic=None):
        """
        Publishes the given Event to the given Topic
        :param event: Event to publish
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        if topic is None:
            topic = event.__class__
        ret = self._publish(event, topic)
        self.on_publish(event, topic)
        return ret

    def subscribe(self, topic):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to this
        Application via the on_event() callback.
        :param topic: the Topic to subscribe to
        :return: a True-ish object if successful
        """
        ret = self._subscribe(topic)
        self.on_subscribe(topic)
        return ret

#TODO: this abstraction nonsense
#class Application(circuits.Component, AbstractApplication):
#    """This class implements the Application using the circuits library"""

    # def __init__(self):
    #     circuits.Component.__init__()

    #######################
    # NOTE: we have to implement these with separate functions in order to use the handler decorator
    #######################

    @handler("SensedEvent")
    def _on_event(self, event, *args):
        """
        This callback is where you should handle the Application's logic for responding to events to which it has
        subscribed.
        :param event: the Event just published
        :param topic: the Topic the Event was published to
        """
        self.on_event(event, "SensedEvent")

    @handler("started")
    def _on_start(self, component):
        """
        This callback is fired as soon as the Application is started.  Use it to handle any setup such as network
        connections, constructing classes, or subscribing to event Topics.
        """
        self.on_start()

    @handler("stopped")
    def _on_stop(self, component):
        """
        This callback is fired when an Application is shut down (including when the whole system is doing so).  Use it
        to free any resources, close network connections, save state, etc.
        """
        self.on_stop()

    def _publish(self, event, topic):
        """
        Publishes the given Event to the given Topic
        :param event: Event to publish
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        return self.fireEvent(event, topic)

    def _subscribe(self, topic):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to this
        Application via the on_event() callback.
        :param topic: the Topic to subscribe to
        :return: a True-ish object if successful
        """
        # TODO: this is going to be near-impossible with circuits alone since they've adopted the convention of
        # subscribing by class type.  This doesn't allow hierarchies like "subscribe to all network-related events",
        # let alone the advanced content-based subscriptions that we're going to want eventually... maybe channels???
        raise NotImplementedError()
        self.addHandler(f)

    # TODO: determine what to do with this part of the API
    # def run(self):
    #     """
    #     This should always be called to start the Application.  You should expect, but not rely on, implementations of
    #     Application to make this function asynchronous, that is it will likely return immediately and do the actual
    #     starting up in the background.
    #     :return: a True-ish object if successful
    #     """
    #     return super(self.__class__, self).run()