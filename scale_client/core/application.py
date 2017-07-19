# note that we'll always keep around a 'handler' decorator even if we stop using circuits!
from circuits.core.handlers import handler
from circuits.core.components import BaseComponent
from circuits.core.timers import Timer
from circuits import Event

import logging
log = logging.getLogger(__name__)


# TODO: have smart choosing of implementations where multiple classes are implemented in this module and
# the one true "Application" implementation is exported as whichever the best of those is that can be imported
# (or that is specified in config?).  It seems that handling this exporting in core/__init__.py will lead to issues
# when another class, e.g. event_reporter, wants to import Application as relative imports apparently cannot be used
# in a non-package

class AbstractApplication(object):
    """
    Applications may subscribe to events and may respond to them
    (or some internal logic) by publishing events.
    These are the core of the system and any classes adding additional
    functionality should at least indirectly subclass Application.
    """

    def __init__(self, broker, **kwargs):
        """
        :param broker: the broker used for the internal pub-sub feature core to the scale_client
        :param kwargs: used for passing args to other constructors when doing multiple inheritance
        """
        super(AbstractApplication, self).__init__()

        self._register_broker(broker)

    # TODO: get_name()?

    def _register_broker(self, broker):
        """Connects this Application to the specified pub-sub event broker.  This method is automatically called for
        you and should really only be used for testing purposes.
        """
        self._broker = broker

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
        Publishes the given Event to the given Topic; then calls on_publish
        :param event: Event to publish
        :param topic: Topic to publish to
        :return: a True-ish object if successful
        """
        if topic is None:
            topic = event.__class__
        ret = self._publish(event, topic)
        self.on_publish(event, topic)

        return ret

    def _publish(self, event, topic):
        """Actual implementation of publishing, which may be different depending on the broker."""
        return self._broker.publish(event, topic)

    def subscribe(self, topic):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to this
        Application via the on_event() callback.  Calls on_subscribe afterwards.
        :param topic: the Topic to subscribe to
        :return: a True-ish object if successful
        """
        ret = self._subscribe(topic)
        self.on_subscribe(topic)
        return ret

    def _subscribe(self, topic):
        """Actual implementation of subscribing, which may be different depending on the broker."""
        return self._broker.subscribe(topic)

    def timed_call(self, time, function, repeat=False, *args, **kwargs):
        """
        This function will call the given function, with the given args,
        once the timer expires.  You can have the timer reset so the
        function will runrepeatedly by using the repeat argument.
        NOTE: the function must be an instancemethod of the calling class!
        NOTE: there is currently no way to cancel the call so if you need
        that feature, add it yourself!

        :param time: time (in seconds or as a datetime object) until
        the timer expires and calls the function
        :param function: function to call
        :param repeat: whether or not the timer should reset and periodically repeat the function
        """
        raise NotImplementedError

    def run(self):
        """
        This should always be called to start the Application.  You should expect, but not rely on, implementations of
        Application to make this function asynchronous, that is it will likely return immediately and do the actual
        starting up in the background.
        :return: a True-ish object if successful
        """
        raise NotImplementedError


################### CIRCUITS IMPLEMENTATION  #############################


class timer_expired_event(Event):
    """Used in circuits implementation to periodically tell an Application to call some function."""


class CircuitsApplication(AbstractApplication, BaseComponent):
    """This class implements the Application using the circuits library"""

    def __init__(self, broker, **kwargs):
        """
        :param broker: the broker used for the internal pub-sub feature core to the scale_client
        :param kwargs: used for passing args to other constructors when doing multiple inheritance
        """
        # NOTE: the circuits channel must be set to THIS instance so that the events fired
        # only affect it and not other Application instances.
        super(CircuitsApplication, self).__init__(broker=broker, channel=self._get_channel_name(), **kwargs)

    def _register_broker(self, broker):
        AbstractApplication._register_broker(self, broker)
        self.register(broker)

    #######################
    # NOTE: we have to implement these with separate functions in order to use the handler decorator
    #######################

    # make sure to do channel * to override the fact that we explicitly set all Components' channels
    @handler("SensedEvent", channel='*')
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

    def timed_call(self, time, function, repeat=False, *args, **kwargs):
        """
        This function will call the given function, with the given args,
        once the timer expires.  You can have the timer reset so the
        function will runrepeatedly by using the repeat argument.
        NOTE: the function must be an instancemethod of the calling class!
        NOTE: there is currently no way to cancel the call so if you need
        that feature, add it yourself!

        :param time: time (in seconds or as a datetime object) until
        the timer expires and calls the function
        :param function: function to call (WARNING: use self.__class__.fun not self.fun)
        :param repeat: whether or not the timer should reset and periodically repeat the function
        """

        # First build a handler for the event that will be fired by the timer
        # and register it with circuits only on our object's unique channel
        # BEWARE: there are some serious dragons here... This is a bunch of
        # hacky nonsense I had to do to convince the circuits system that the
        # function we're passing them is a bona-fide handler object.  For
        # whatever reason, we can't just pass the instancemethod directly to
        # the handler function to make a handler as we get some AttributeError
        # related to it trying to set attributes that don't exist, so instead
        # we have to provide a regular method here that wraps the actual
        # instancemethod.
        def f(*fargs, **fkwargs):
            return function(*fargs, **fkwargs)
        f = handler(False, channel=self._get_channel_name(), override=True)(f)
        f.handler = True
        f.names = ["timer_expired_event"]
        f.channel = self._get_channel_name()
        f.priority = 10
        f.event = False
        self.addHandler(f)

        # Then set the timer.  Note how the args are passed via the
        # __timer_expired_event object.
        self._timer = Timer(time, timer_expired_event(*args, **kwargs), self._get_channel_name(), persist=repeat)
        self._timer.register(self)

        # TODO: allow cancelling the timed_call by returning a reference to
        # the handler we registered and write a cancel_timed_call(method)
        # function that takes this reference in and calls removeHandler

    def _get_channel_name(self):
        """
        Returns a channel name to be used by circuits for routing events properly.
        Currently just the class name plus the unique memory address.
        :return:
        """
        return '%s@%d' % (self.__class__.__name__, id(self))

# Lastly, we set the default Application
Application = CircuitsApplication