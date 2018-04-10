import json
import logging
log = logging.getLogger(__name__)
import time

from scale_client.sensors.virtual_sensor import VirtualSensor


class DummyVirtualSensor(VirtualSensor):
    """
    A DummyVirtualSensor generates dummy data (useful for testing) in a configurable manner.
    Future versions will support dynamically-generated SensedEvent data and a dynamic sample_interval.
    """

    def __init__(self, broker, sample_interval=1,
                 # new parameters
                 start_delay=0, start_time=None, output_events_file=None,
                 static_event_data="dummy_data", dynamic_event_data=None, **kwargs):
        """
        :param broker:
        :param sample_interval: set to 1 second by default for generating basic dummy data; set to None to disable synchronous mode
        :param start_delay: on_start will be delayed by this many seconds
        :param start_time: on_start will be delayed until the specified time (in Unix Epoch timestamp format).
          NOTE: you cannot use both start_delay and start_time!
        :param output_events_file: when specified, save each created SensedEvent to the requested file,
        which will be a JSON-encoded list of events
        :param static_event_data: every sensor read will return this exact data
        :param dynamic_event_data: configure sending dynamic data, which will override static_event_data;
         see _get_dynamic_data() for details
        :param kwargs:
        """
        super(DummyVirtualSensor, self).__init__(broker, sample_interval=sample_interval, **kwargs)

        self.start_delay = start_delay
        self.start_time = start_time
        if start_delay != 0 and start_time is not None:
            raise ValueError("cannot specify both start_delay and start_time!")

        self.static_event_data = static_event_data
        self.dynamic_event_data = dynamic_event_data

        # If we enabled event logging to file, start a list we'll append each new one in
        self.output_events_file = output_events_file
        if self.output_events_file is not None:
            self.__output_events = []
        else:
            self.__output_events = None

    def read_raw(self):
        if self.dynamic_event_data is not None:
            return self._get_dynamic_data(self.dynamic_event_data)
        return self.static_event_data

    def _get_dynamic_data(self, dynamic_data):
        """
        Based on the input dynamic_data configuration dict, return the next piece of dynamic data.
        Possible options are:
           -  {'seq': start} (increasing sequence # starting at start)

        :param dynamic_data:
        :type dynamic_data: dict
        :return:
        """

        # ENHANCE: actually use an object for getting each new piece of data rather than this hacky field storage?
        if 'seq' in dynamic_data:
            if not hasattr(self, '_dyn_seq'):
                self._dyn_seq = dynamic_data['seq']
            val = self._dyn_seq
            self._dyn_seq += 1
            return val
        else:
            raise ValueError("unrecognized dynamic data configuration: %s" % dynamic_data)

    def on_publish(self, event, topic):
        super(DummyVirtualSensor, self).on_publish(event, topic)
        if self.__output_events is not None:
            self.__output_events.append(event)

    def on_stop(self):
        super(DummyVirtualSensor, self).on_stop()
        if self.output_events_file:
            with open(self.output_events_file, 'w') as f:
                # since we don't have an actual SensedEvent encoder, just convert each to a map first
                f.write(json.dumps([e.to_map() for e in self.__output_events], indent=2))

    def on_start(self):
        """
        Optionally delays the VirtualSensor.on_start method.
        :return:
        """

        # TODO: anything different for dynamic_event_data?
        if self.start_delay > 0:
            log.debug("delaying on_start by %d seconds" % self.start_delay)
            self.timed_call(self.start_delay, VirtualSensor.on_start)
        elif self.start_time is not None:
            delay = self.start_time - time.time()
            if delay > 0:
                log.debug("delaying on_start by %d seconds" % delay)
                self.timed_call(delay, VirtualSensor.on_start)
            else:
                log.error("cannot delay on_start as start_time is before the current time!")
        else:
            super(DummyVirtualSensor, self).on_start()