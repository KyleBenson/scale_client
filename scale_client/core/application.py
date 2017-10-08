# note that we'll always keep around a 'handler' decorator even if we stop using circuits!
import inspect

from circuits.core.handlers import handler
from circuits.core.components import BaseComponent
from circuits.core.timers import Timer
from circuits import Event

import logging

import scale_client.core.sensed_event
from scale_client.util import uri

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

    # TODO: also allow optionally-specified handlers other than on_event
    def __init__(self, broker, subscriptions=tuple(), advertisements=tuple(),
                 name=None, **kwargs):
        """
        :param broker: the broker used for the internal pub-sub feature core to the scale_client
        :param subscriptions: list of topics this app subscribes to and will handle with on_event()
        :param advertisements: list of topics this app may publish to / event types it might publish
               NOTE: the first advertised topic is the assumed default event_type for make_event()
        :param name: unique human-readable name for this Application
        :param kwargs: used for passing args to other constructors when doing multiple inheritance
        """
        # XXX: passing kwargs lets us multiply inherit from other circuits components
        super(AbstractApplication, self).__init__(**kwargs)
        # HACK: BUGFIX: circuits-specific: it never actually 'pops' the channel kwargs in its __init__
        if __debug__:
            kwargs.pop('channel')
            if len(kwargs) != 0:
                log.debug("kwargs should be empty by this point since AbstractApplication is just an object! "
                          "This may be due to circuits kwargs propagating all the way here, but double-check "
                          "you didn't miss-spell a parameter! Remaining kwargs are: %s" % kwargs)

        self._broker = None  # for auto completion
        self._register_broker(broker)
        # We currently assume this will never be changed!
        if name is None:
            self.__name = self.__class__.__name__
        else:
            self.__name = name

        # store all timer objects used for self.timed_call() so we can cancel them on_stop()
        self._timers = []
        self._topic_subscriptions = list(subscriptions)
        # TODO: something useful other than just setting these in sensors...
        self._topic_advertisements = list(advertisements)

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        """
        Get the canonical path for this Application as determined by its name and any user-specified
        path components from derived class implementations.
        :return:
        """
        return uri.build_uri(relative_path="applications/%s" % self.name)

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
        By default, it will subscribe to all (if any) subscription topics were specified in the constructor.
        Depending on the concrete Application implementation, you may need to cancel any active timers.
        """
        for t in self._topic_subscriptions:
            self.subscribe(t)

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

    def make_event(self, source=None, event_type=None, **kwargs):
        """
        Creates a SensedEvent passing kwargs directly to the constructor but filling it in with missing details
        based on this Application's logic/state.  See its implementation for the default values it sets.
        Override this function to customize the events you create
        (e.g. call super with additional default kwargs set or even use a Factory).

        :param kwargs:
        :param source: defaults to self.path
        :param event_type: defaults to the first of our topic advertisements or else to self.name if we have none
        :return: SensedEvent
        """
        if source is None:
            source = self.path
        if event_type is None:
            # First advertised topic is assumed the default for making events
            if self._topic_advertisements:
                event_type = self._topic_advertisements[0]
            # Otherwise we can at least have SOMETHING set...
            else:
                event_type = self.name
        return scale_client.core.sensed_event.SensedEvent(source=source, event_type=event_type, **kwargs)

    #TODO: unsubscribe?

    def publish(self, event, topic=None):
        """
        Publishes the given Event to the given Topic; then calls on_publish
        :param event: Event to publish
        :type event: scale_client.core.sensed_event.SensedEvent
        :param topic: Topic to publish to (optional; default=event.__class__.__name__)
        :return: a True-ish object if successful
        """
        if topic is None:
            try:
                topic = event.topic
            except AttributeError:
                topic = event.__class__.__name__
        ret = self._publish(event, topic)
        self.on_publish(event, topic)

        return ret

    def _publish(self, event, topic):
        """Actual implementation of publishing, which may be different depending on the broker."""
        return self._broker.publish(event, topic)

    def subscribe(self, topic, callback=None):
        """
        Subscribes to the given Topic so that any Events being published to that Topic will be routed to this
        Application via the on_event() callback.  Calls on_subscribe afterwards.
        :param topic: the Topic to subscribe to
        :param callback: optional callback to fire with the newly published Event as its argument (default=self.on_event)
        :return: a True-ish object if successful
        """
        if callback is None:
            callback = self.on_event
        ret = self._subscribe(topic, callback)
        # TODO: should probably pass the return value here so we can handle errors with it
        self.on_subscribe(topic)
        return ret

    def _subscribe(self, topic, callback):
        """Actual implementation of subscribing, which may be different depending on the broker."""
        return self._broker.subscribe(topic, callback)

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

    @handler("started")
    def _on_start(self, component):
        """
        This callback is fired as soon as the Application is started.  Use it to handle any setup such as network
        connections, constructing classes, or subscribing to event Topics.
        """
        self.on_start()

    @handler("signal")
    def _on_signal(self, signo, frame):
        """
        This callback is fired when an interrupt signal is sent through the system (e.g. SIGINT).
        Since it doesn't seem to always issue the "stopped" event correctly, this is basically
        a hack to make sure that it stops everything.
        :param signo:
        :param frame:
        :return:
        """
        self._broker.stop()

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

        :param time: time (in seconds or as a datetime object) until
        the timer expires and calls the function
        :param function: function to call (WARNING: use self.__class__.fun not self.fun)
        :param repeat: whether or not the timer should reset and periodically repeat the function
        :returns: the Timer object used to manage this timed_call (cancel with Timer.stop())
        """

        # First build a handler for the event that will be fired by the timer
        # and register it with circuits only on our object's unique channel
        # The channel is also unique to this function so that we can support
        # multiple outstanding timed_calls simultaneously.
        # TODO: test said support!
        timer_class_name = timer_expired_event.__name__
        timer_channel = "%s/%s/%s" % (self._get_channel_name(), timer_class_name, id(function))
        self.subscribe(timer_channel, data_spaces=[timer_class_name], callback=function)

        # Then set the timer.  Note how the args are passed via the timer_expired_event object.
        t = Timer(time, timer_expired_event(*args, **kwargs), timer_channel, persist=repeat)
        self._timers.append(t)
        t.register(self)
        return t

    # TODO: since inheritance cannot be directly used with SensedEvent
    # (i.e. have all derived event types show up to to this callback), here's a
    # Thought on how to do this: accept either strings or SensedEvent instances or classes (issubclass?);
    # just get that class's __name__ if None specified
    # Could make use of SensedEvent's .topic property to get the actual class name and have that get
    # passed around to subscribe calls, etc.
    def subscribe(self, topic, callback=None, data_spaces=None):
        """
        Subscribe to the given topic such that the specified callback is called when an event matching that topic
        is published.
        :param topic: topic string to subscribe to or an Event instance that we'll extract a topic from
        :param callback: an unbound method of the subscribing class that accepts just self and the Event
             being published (default=self.on_event(event, event.event_type))
        :param data_spaces: a string representing the 'data space' you're interested in e.g. for SensedEvents.
          This is used to separate different event types from each other.
        circuits-specific note: these must be the actual class name of the Event type
        (default=SensedEvent.__name__ when topic is a string, topic.__class__.__name__ when it's a class:
        so you can typically ignore this parameter unless you subclass SensedEvent)
        :raises ValueError: when callback is an instancemethod rather than an unbound one;
                 instead use self.__class__.fun not self.fun
        :return:
        """

        # Handle possibility of topic being an Event instance rather than string
        if isinstance(topic, Event):
            # First get data space if needed
            if data_spaces is None:
                data_spaces = (topic.__class__.__name__,)
            # Now extract actual topic or just use the class name as default one
            try:
                topic = topic.topic
            except AttributeError:
                topic = topic.__class__.__name__

        # Set 'data_spaces' param default
        if data_spaces is None:
            data_spaces = (scale_client.core.sensed_event.SensedEvent.__name__,)

        # XXX: In order to call on_event(), we need to pass it the event_type (topic) too!
        if callback is None:
            def callback(myself, the_event):
                return myself.on_event(the_event, the_event.event_type)
        # XXX: Because specifying an instancemethod will cause an error due to another
        # self parameter being bound in by circuits in self.addHandler, we should
        # raise this error prematurely since circuits doesn't give a very helpful error message...
        elif inspect.ismethod(callback) and callback.im_self:
            raise ValueError("ERROR: specified callback is an instancemethod but we need an unbound method!"
                             "Please use self.__class__.fun not self.fun")

        # BEWARE: there are some serious dragons here... This is a bunch of
        # hacky nonsense I had to do to convince the circuits system that the
        # callback we're passing them is a bona-fide handler object.  We can't
        # just pass the instancemethod directly to the handler callback to make
        # a handler as we get an AttributeError due to it setting a non-existing
        # attribute. Functions, but not instancemethods apparently, can have
        # arbitrary attributes added in Python so we have to wrap the latter
        # with the former.
        def f(*fargs, **fkwargs):
            return callback(*fargs, **fkwargs)

        # override=True ensures if a base class redefines an event handler it will be
        # called separately instead of as an additional handler for the event
        f = handler(*data_spaces, channel=topic, override=True)(f)
        self.addHandler(f)

        self.on_subscribe(topic)

        return f

    def _get_channel_name(self):
        """
        Returns a channel name to be used by circuits for routing events properly.
        Currently just the class name plus the unique memory address.
        We use this to create a channel unique to this object instance so e.g.
        a timed_call event won't fire to other objects.
        :return:
        """
        return '%s@%d' % (self.__class__.__name__, id(self))

# Lastly, we set the default Application
Application = CircuitsApplication