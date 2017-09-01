from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent
from scale_client.util import uri

import logging

log = logging.getLogger(__name__)


class VirtualSensor(Application):
    """
    VirtualSensors represent an abstract sensor feed, which may be raw data coming directly
     from a device, data coming from a remote device, or even events detected by other VirtualSensors.
    The main idea is that a VirtualSensor obscures the details of how, where, and when sensor
    data is collected.  This leaves the developer to implement such logic only when necessary and
    as late as possible in the 'data collection pipeline'.  Additionally, the user can (re)configure
    a VirtualSensor using various available parameters in order to customize its behavior for the
    given deployment or even dynamic real-time scenarios.

    Keep in mind that a VirtualSensor is a specific type of Application.  When implementing a new VirtualSensor,
    you may want to make use of functions such as on_start() to initiate connections to any 'physical' sensor devices,
    which may include opening connections to e.g. USB devices.  Use a VirtualSensor when you want to make use of its
    added convenience functions, none of which are necessary to implement.
    See __init__ for details about configuring a VirtualSensor to use these extensions to Application,
    notably the periodic sensor reading method.

    Open implementation questions:
      1) How to handle sampling rates, modifying priorities, and turning sensors on/off remotely?
    """

    DEFAULT_PRIORITY = 5

    def __init__(self, broker, sample_interval=None, event_type=None, **kwargs):
        """
        Configures the VirtualSensor in one of three sensing modes:

        synchronous: read() called every sample_interval seconds
        asynchronous: on_event called whenever an event matching the specified 'subscriptions' occurs (note that this is the same behavior as a class Application)
        stream: not currently implemented!  This will eventually use a queue for sensor data expected in streams rather than less-frequent discrete events.

        :param broker:
        :param sample_interval: the sensor will read() every sample_interval seconds (synchronous mode) if not None (default)
        :param event_type: short string used like the type of sensor or topic it publishes events to e.g. temperature
                NOTE: the event topic specified, if any, will be passed along as an advertisement
        :raises ValueError: if parameters don't successfully configure one of the three modes
        :param kwargs:
        """
        # XXX for backwards compatibility
        if 'interval' in kwargs:
            if sample_interval is not None:
                log.warning("sample_interval is now used for telling a VirtualSensor its period data reading interval,"
                            " but you specified both sample_interval=%f and interval=%f!"
                            "We'll use the 'interval' value since you likely specified it in a config file..." \
                            % (sample_interval, kwargs['interval']))
            sample_interval = kwargs.pop('interval')

        # We use the event_type as the default type for making SensedEvents by passing
        # it as the first (and likely only) publication advertisement.
        ads = kwargs.get('advertisements', tuple())
        if event_type is not None:
            if not ads:
                ads = (event_type,)
            elif ads:
                new_ads = list((event_type,))
                new_ads.extend(ads)
                ads = new_ads

        super(VirtualSensor, self).__init__(broker, advertisements=ads, **kwargs)

        # Check that at least one mode has been chosen
        # We can't raise an assertion like this as some sensors may be configured for hardware-based
        # asynchronous mode (rather than through our pub-sub system).
        if not kwargs.get('subscriptions') and sample_interval is None:
            log.debug("NOTE: Invalid parameters failed to enable the sensor in (a)synchronous mode:"
                      " subs=%s, interval=%s\nHopefully you enabled a hardware-based async mode"
                      " or you might encounter threading problems!" %
                      (kwargs.get('subscriptions'), sample_interval))

        self._sample_interval = sample_interval
        # used to track and possibly cancel the timer used for synchronous mode
        self._sensor_timer = None

    @property
    def path(self):
        """
        Get the canonical path for this Application as determined by its name and any user-specified
        path components from derived class implementations.
        :return:
        """
        return uri.build_uri(relative_path="sensors/%s" % self.name)

    def read_raw(self):
        """
        Most VirtualSensors are designed to read data periodically.  Here is where you implement that logic, if
        necessary, to return a raw sensor reading.
        :return: raw data
        """
        raise NotImplementedError

    def read(self):
        """
        This calls read_raw() to read sensor data and then packages that data in a SensedEvent.  Override this function
        to add additional fields to or modify the resulting SensedEvent.
        :return:
        """
        data = self.read_raw()
        return self.make_event(data=data)

    def make_event(self, priority=None, condition=None, **kwargs):
        """
        Make a SensedEvent with the assigned default parameters specified in the class implementation.
        :param priority:
        :param condition: default will specify either the interval or the subscriptions
        :param kwargs:
        :return:
        """
        if priority is None:
            priority = self.__class__.DEFAULT_PRIORITY
        if condition is None:
            if self._sample_interval is not None:
                condition = {'interval': self._sample_interval}
            elif self._topic_subscriptions:
                condition = {'topic_subscriptions': self._topic_subscriptions}
            else:
                log.error("couldn't set condition from either sample interval or topic subscriptions:"
                          " this shouldn't happen in a properly configuration!")
        return super(VirtualSensor, self).make_event(priority=priority, condition=condition, **kwargs)

    def make_event_with_raw_data(self, raw_data, priority=None):
        """
        DEPRECATED: you should just use Application.make_event(**kwargs) instead
        This function returns a new SensedEvent that contains the raw data specified packaged in the SensedEvent.data
        instance variable.  Override this method to tweak your custom SensedEvent.

        :param raw_data: raw data string or bytes
        :param priority: priority to assign this event (None uses the class default)
        :return: SensedEvent
        """
        event = self.make_event(data=raw_data, priority=priority)
        return event

    def set_sample_interval(self, period=1):
        """
        Accepts a datetime object, or number of seconds, representing how long the VirtualSensor should wait before
        reading data each time.  The default is 1 second.  The timer will be immediately reset by this call.
        :return:
        """
        self._sample_interval = period
        try:
            # WARNING: circuits-specific!
            self._sensor_timer.reset(self._sample_interval)
        except AttributeError:
            pass

    def policy_check(self, event):
        """
        A VirtualSensor may choose whether or not to publish a new SensedEvent.  This function returns True if the given
        event should be published, False otherwise.  By default, it will always return True.
        :param event:
        :return: bool
        """
        return True

    def _do_sensor_read(self):
        """
        This function actually reads sensor data and then publishes it if it passes the policy_check()
        """

        try:
            event = self.read()
        except IOError as e:
            log.debug("%s failed read sensor data! reason: %s" % (self.name, e))
            return

        log.debug("%s read sensor data. raw value: %s" % (self.name, event.data))
        if event is None:
            log.error("SensedEvent is None! Default policy is to not report.")
            return
        if self.policy_check(event):
            self.publish(event)

    def on_start(self):
        """
        Override this function to initiate connections to any 'physical' sensor devicess.
        Don't forget to call this version, though, if you want to make use of the
        periodic sensing feature, which will continually read data at the rate specified by the interval constructor arg,
        publishing any SensedEvents gleaned from read() if they pass policy_check().
        To use this feature, do the following at the end of your implementation: super(YourSensorClass, self).on_start()
        """
        super(VirtualSensor, self).on_start()
        if self._sample_interval is None:
            return
        self._do_sensor_read()
        # We make an effort to get the child class's _do_sensor_read method in case they override it.
        t = self.timed_call(self._sample_interval, self.__class__._do_sensor_read, repeat=True)
        self._sensor_timer = t
