from scale_client.core.sensed_event import SensedEvent
from scale_client.stats.random_variable import RandomVariable

# This makes publications easier to work with in external modules
from collections import namedtuple
Publication = namedtuple("Publication", ['topic', 'time', 'data'])


class SensedEventGenerator(object):
    """
    Generates random SensedEvents from a data stream (i.e. event topic, creation time, size of random data)
    that is generated from specified distributions. This can be used to make a collection of random data or even
    the events published by a `DummyVirtualSensor` that generates random events from
    various probability distributions.

    NOTE on probability distributions: if a parameter claims to accept 'distribution kwargs', the value should be
    a dict that matches the signature of build_random_distribution()
    """

    def __init__(self):
        super(SensedEventGenerator, self).__init__()

    def generate_publications(self, topic, publication_period, data_size=1, data_size_bounds=(1, 10000),
                              nevents=None, total_time=None):
        """
        This generator yields raw publication data in the form of a tuple containing:
          - topic
          - time (in seconds as a float) until this event should be published
          - data (a sequence # formatted as a string of the length drawn from the data_size distribution)

        NOTE: generation goes on indefinitely until the first of the optional parameters nevents or total_time are reached.

        :param topic: the topic is static across all publications
        :param publication_period: an int or random distribution kwargs to determine the period between publications
        :param data_size: either an int or random distribution kwargs to determine the number of random chars
        :param data_size_bounds: 2-tuple of (lower, upper) bounds for the data size
        :param nevents: the number of total events to generate before stopping (use this if you're making a list!)
        :param total_time: generation stops after the total publication times reach this value (use this for making lists!)
        :rtype: generator[Publication]
        :return:
        """

        timespan_covered = 0
        total_events = 0

        rand_period = False
        if isinstance(publication_period, dict):
            # bound it to 1ms minimum
            publication_period.setdefault("lbound", 0.001)
            publication_period.setdefault("ubound", total_time)
            rand_period = RandomVariable(**publication_period)

        rand_size = False
        if isinstance(data_size, dict):
            data_size.setdefault("lbound", data_size_bounds[0])
            data_size.setdefault("ubound", data_size_bounds[1])
            rand_size = RandomVariable(**data_size)

        td = publication_period
        while (nevents is None or nevents > total_events) and (total_time is None or total_time > timespan_covered):
            if rand_period:
                td = rand_period.get()

            timespan_covered += td
            if total_time is not None and timespan_covered > total_time:
                break  # to avoid generating events past the timespan requested

            # TODO: how to accept a param for generating the actual data?  maybe do a self.get_random_data(size)?
            if rand_size:
                data_size = rand_size.get_int()
            # value of event should end up being a sequence number by default
            # XXX: requesting too large of a formatted integer causes an OverflowError, however,
            #   so start smaller and add 0's if needed:
            if data_size > 100:
                fmt_data_size = 100
            else:
                fmt_data_size = data_size

            data = ("%%.%dd" % fmt_data_size) % total_events

            if data_size != fmt_data_size:
                data = ('0' * (data_size - fmt_data_size)) + data

            yield Publication(topic, td, data)
            total_events += 1

    def generate_sensed_events(self, *args, **kwargs):
        """
        Accepts args of generate_publications or get_sensed_events_from_publications (other than 'publications' of course)
        but generates actual SensedEvent objects.
        :rtype: generator[SensedEvent]
        """

        init_time = kwargs.pop('init_time', None)
        source = kwargs.pop('source', None)
        metadata = kwargs.pop('metadata', None)
        return self.get_sensed_events_from_publications(self.generate_publications(*args, **kwargs),
                                                        init_time=init_time, source=source, metadata=metadata)

    @classmethod
    def get_sensed_events_from_publications(cls, publications, init_time=None, source=None, metadata=None):
        """
        Converts the output from generate_publications() into SensedEvents
        :param publications:
        :param init_time: the time until event publication is added to this to create a complete timestamp (default is now)
        :param source: optional source to set in the SensedEvent
        :param metadata: optional metadata to set
        :rtype: generator[SensedEvent]
        :return:
        """

        if init_time is None:
            init_time = SensedEvent.get_timestamp()

        for pub in publications:
            init_time += pub.time
            yield SensedEvent(pub.data, source=source, event_type=pub.topic, timestamp=init_time, metadata=metadata)


    # ENHANCE:
    # @staticmethod
    # def interleave_events(*event_collections):
    #     """
    #     Interleaves the list-like collections of SensedEvents such that the resulting list is ordered by time.
    #     :param event_collections:
    #     :return:
    #     """