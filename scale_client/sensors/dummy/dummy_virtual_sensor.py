import json
import logging
log = logging.getLogger(__name__)

from scale_client.sensors.virtual_sensor import VirtualSensor


class DummyVirtualSensor(VirtualSensor):
    """
    A DummyVirtualSensor generates dummy data (useful for testing) in a configurable manner.
    Future versions will support dynamically-generated SensedEvent data and a dynamic sample_interval.
    """

    def __init__(self, broker, sample_interval=1,
                 # new parameters
                 start_delay=0, output_events_file=None,
                 static_event_data="dummy_data", dynamic_event_data=None, **kwargs):
        """
        :param broker:
        :param sample_interval: set to 1 second by default for generating basic dummy data; set to None to disable synchronous mode
        :param start_delay: on_start will be delayed by this many seconds
        :param output_events_file: when specified, save each created SensedEvent to the requested file,
        which will be a JSON-encoded list of events
        :param static_event_data:
        :param dynamic_event_data:
        :param kwargs:
        """
        super(DummyVirtualSensor, self).__init__(broker, sample_interval=sample_interval, **kwargs)

        if dynamic_event_data is not None:
            raise NotImplementedError("currently no support for dynamic_event_data")

        self.start_delay = start_delay
        self.static_event_data = static_event_data

        # If we enabled event logging to file, start a list we'll append each new one in
        self.output_events_file = output_events_file
        if self.output_events_file is not None:
            self.__output_events = []
        else:
            self.__output_events = None

    def read_raw(self):
        # TODO: handle dynamic_event_data
        return self.static_event_data

    def read(self):
        event = super(DummyVirtualSensor, self).read()
        if self.__output_events is not None:
            self.__output_events.append(event)
        return event

    def on_stop(self):
        super(DummyVirtualSensor, self).on_stop()
        if self.output_events_file:
            with open(self.output_events_file, 'w') as f:
                # since we don't have an actual SensedEvent encoder, just convert each to a map first
                f.write(json.dumps([e.to_map() for e in self.__output_events]))

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