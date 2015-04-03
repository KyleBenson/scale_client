from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import logging
log = logging.getLogger(__name__)

from circuits.core.events import Event
from circuits.core.timers import Timer
from circuits.core.handlers import handler
from circuits.core.components import BaseComponent

class ReadSensorData(Event):
    """Used in circuits implementation to periodically tell a VirtualSensor to call its read() function."""


class VirtualSensor(Application):
    """
    VirtualSensors represent an abstract sensor feed, which may be raw data coming directly from a device, data
    coming from a remote device, or even events detected by other VirtualSensors.

    Keep in mind that a VirtualSensor is a specific type of Application.  When implementing a new VirtualSensor,
    you may want to make use of functions such as on_start() to initiate connections to any 'physical' sensor devices,
    which may include opening connections to e.g. Twitter feeds.  Use a VirtualSensor when you want to make use of its
    added convenience functions, none of which are necessary to implement.

    Open implementation questions:
      1) How to handle sampling rates, modifying priorities, and turning sensors on/off remotely?
    """
    # TODO: verify that this can be overridden by base classes and function properly.  also document
    DEFAULT_PRIORITY = 5

    def __init__(self, broker, device=None, interval=1):
        # NOTE: this circuits-specific hack helps deliver events only to the right channels, that is ReadSensorData
        # events will only fire to the object that initiated the timer that fires them.  Also note that it MUTS come
        # before the super() call!
        BaseComponent.__init__(self, channel=self.__get_channel_name())
        super(VirtualSensor, self).__init__(broker)

        # TODO: anonymous device descriptor?
        self.device = device
        self._wait_period = interval

    def get_type(self):
        """
        A unique human-readable identifier of the type of sensor this object represents.
        """
        return "VirtualSensor"

    def read_raw(self):
        """
        Most VirtualSensors are designed to read data periodically.  Here is where you implement that logic, if
        necessary, to return a raw sensor reading.
        :return: raw data
        """
        return "SensedEvent"

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

        :param data: raw data string or bytes
        :return: SensedEvent
        """
        if priority is None:
            priority = self.__class__.DEFAULT_PRIORITY
        structured_data = {"event": self.get_type(), "value": raw_data}

        event = SensedEvent(self.get_type() if self.device is None else self.device.device,
                            structured_data, priority)
        return event

    def set_wait_period(self, period):
        """
        Accepts a datetime object, or number of seconds, representing how long the VirtualSensor should wait before
        reading data each time.  The default is 1 second.
        :return:
        """
        self._wait_period = period

    def policy_check(self, event):
        """
        A VirtualSensor may choose whether or not to publish a new SensedEvent.  This function returns True if the given
        event should be published, False otherwise.  By default, it will always return True.
        :param event:
        :return: bool
        """
        return True

    def on_start(self):
        """
        Override this function to initiate connections to any 'physical' sensor devices, which may include opening
        connections to e.g. Twitter feeds.  Don't forget to call this version, though, if you want to make use of the
        periodic sensing feature, which will continually read data at the rate specified by get_next_wait_period(),
        publishing any SensedEvents gleaned from read() if they pass policy_check().
        To use this feature, do the following at the end of your implementation: super(YourSensorClass, self).on_start()
        """
        self._timer = Timer(self._wait_period, ReadSensorData(), self.__get_channel_name(), persist=True)
        self._timer.register(self)

    @handler("ReadSensorData")
    def _do_sensor_read(self):
        """
        This function actually reads sensor data and then publishes it if it passes the policy_check()
        """
        log.debug("ReadSensorData event received; reading...")

        event = self.read()
        if event is None:
            log.error("SensedEvent is None! Default policy is to not report.")
            return
        if self.policy_check(event):
            # we specify the event's class because that is how topics are currently implemented using circuits
            self.publish(event)

    def __get_channel_name(self):
        """
        Returns a channel name to be used by circuits for routing events properly.  Currently just the class name.
        :return:
        """
        # TODO: make this instance unique so e.g. two Heartbeat sensors could run at once
        return self.__class__.__name__