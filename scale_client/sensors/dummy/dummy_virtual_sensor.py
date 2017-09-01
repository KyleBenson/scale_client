import logging
log = logging.getLogger(__name__)

from scale_client.sensors.virtual_sensor import VirtualSensor


class DummyVirtualSensor(VirtualSensor):
    """
    A DummyVirtualSensor generates dummy data (useful for testing) in a configurable manner.
    Future versions will support dynamically-generated SensedEvent data and a dynamic sample_interval.
    """

    def __init__(self, broker, start_delay=0, sample_interval=1, static_event_data="dummy_data", dynamic_event_data=None, **kwargs):
        """
        :param broker:
        :param start_delay: on_start will be delayed by this many seconds
        :param sample_interval: set to 1 second by default for generating basic dummy data
        :param static_event_data:
        :param dynamic_event_data:
        :param kwargs:
        """
        super(DummyVirtualSensor, self).__init__(broker, sample_interval=sample_interval, **kwargs)

        if dynamic_event_data is not None:
            raise NotImplementedError("currently no support for dynamic_event_data")

        self.start_delay = start_delay
        self.static_event_data = static_event_data

    def read_raw(self):
        # TODO: handle dynamic_event_data
        return self.static_event_data

    def on_start(self):
        """
        Optionally delays the VirtualSensor.on_start method.
        :return:
        """

        # TODO: anything different for dynamic_event_data?
        if self.start_delay > 0:
            log.debug("delaying on_start by %d seconds" % self.start_delay)
            self.timed_call(self.start_delay, VirtualSensor.on_start)
        else:
            super(DummyVirtualSensor, self).on_start()