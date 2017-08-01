from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

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

    def __init__(self, broker, data_source=None, sample_interval=None, **kwargs):
        """
        Configures the VirtualSensor in one of three sensing modes:

        synchronous: read() called every sample_interval seconds
        asynchronous: on_event called whenever an event matching the specified 'subscriptions' occurs (note that this is the same behavior as a class Application)
        stream: not currently implemented!  This will eventually use a queue for sensor data expected in streams rather than less-frequent discrete events.

        :param broker:
        :param data_source: used to tag events with the source event (or physical sensing device) that created them (default is to use list of event subscriptions or get_type() if no subscriptions; this can be safely ignored if you will manually set the source(s) for events your VirtualSensor creates)
        :param sample_interval: the sensor will read() every sample_interval seconds (synchronous mode) if not None (default)
        :raises ValueError: if parameters don't successfully configure one of the three modes
        :param kwargs:
        """
        # XXX for backwards compatibility
        if 'interval' in kwargs:
            sample_interval = kwargs.pop('interval')
        super(VirtualSensor, self).__init__(broker, **kwargs)

        # Ensure that at least one mode has been chosen
        if not kwargs.get('subscriptions') and sample_interval is None:
            raise ValueError("Invalid parameters failed to enable the sensor in (a)synchronous mode: subs=%s, interval=%s" % (kwargs.get('subscriptions'), sample_interval))

        self.data_source = data_source
        self._sample_interval = sample_interval
        # used to track and possibly cancel the timer used for synchronous mode
        self._sensor_timer = None

    def get_type(self):
        """
        A unique human-readable identifier of the type of sensor this object represents.
        """
        raise NotImplementedError

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
        return self.make_event_with_raw_data(data)

    def make_event_with_raw_data(self, raw_data, priority=None):
        """
        This function returns a new SensedEvent that contains the raw data specified packaged in the SensedEvent.data
        instance variable.  Override this method to tweak your custom SensedEvent.

        :param raw_data: raw data string or bytes
        :param priority: priority to assign this event (None uses the class default)
        :return: SensedEvent
        """
        if priority is None:
            priority = self.__class__.DEFAULT_PRIORITY
        # TODO: this logic should be handled in the SensedEvent class!
        structured_data = {"event": self.get_type(), "value": raw_data}

        event = SensedEvent(self.data_source, structured_data, priority)
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
            log.debug("%s failed read sensor data! reason: %s" % (self.get_type(), e))
            return

        log.debug("%s read sensor data. raw value: %s" % (self.get_type(), event.get_raw_data()))
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

        @property
        def data_source(self):
            return self.__data_source

        @data_source.getter
        def data_source(self):
            if self.__data_source is not None:
                return self.__data_source
            elif self._topic_subscriptions:
                return {'topic_subscriptions': self._topic_subscriptions}
            else:
                return self.get_type()

        @data_source.setter
        def data_source(self, value):
            self.__data_source = value
