from scale_client.sensors.dummy.dummy_virtual_sensor import DummyVirtualSensor
from scale_client.stats.sensed_event_generator import SensedEventGenerator

import logging
log = logging.getLogger(__name__)


class RandomVirtualSensor(DummyVirtualSensor):
    """
    Generates a SensedEvent stream from RandomVariable distributions.  More complex than a DummyVirtualSensor, this is
    useful for simulating asynchronous events published according to e.g. a Poisson process.  It also supports
    actually modeling the contents of each event according to a RandomVariable.
    """

    def __init__(self, broker, event_generator=None, **kwargs):
        """
        :param broker:
        :param event_generator: configuration for SensedEventGenerator this object uses to create publications that
                will be converted to SensedEvents
        :type event_generator: dict
        :param kwargs:
        """

        # XXX: sample_interval=None disables the periodic sensor sampling mechanism
        super(RandomVirtualSensor, self).__init__(broker, sample_interval=None, **kwargs)

        # We'll just create the generator now and then iterate over them one at a time later.
        # NOTE that we generate publications rather than SensedEvents since we want to ensure this VS object fills in
        #   any requested SensedEvent fields (e.g. priority, metadata, etc.).
        self.event_generator = SensedEventGenerator().generate_publications(**event_generator)
        self.next_event = next(self.event_generator, None)

        # Save the configuration so we can use it as the condition for creating a SensedEvent
        self._condition = event_generator

    def read(self):
        """
        Generates the random event and schedules the next one dynamically.
        :return:
        """

        # TODO: how to support more complex data e.g. multi-dimensional?
        ev = None
        if self.next_event:
            ev = self.make_event(event_type=self.next_event.topic, data=self.next_event.data, condition=self._condition)
            self.next_event = next(self.event_generator, None)

            if self.next_event:
                self.timed_call(self.next_event.time, self.__class__._do_sensor_read)

        return ev

    def on_start(self):
        """
        :return:
        """
        super(RandomVirtualSensor, self).on_start()

        # schedule the next (first) event for publication based on its time
        if self.next_event:
            self.timed_call(self.next_event.time, self.__class__._do_sensor_read)