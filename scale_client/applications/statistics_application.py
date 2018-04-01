import json

from scale_client.core.application import Application
import logging
log = logging.getLogger(__name__)


class StatisticsApplication(Application):
    """
    This Application gathers various aggregate statistics for subscribed events.  These stats can be directly retrieved or even
    written to an output file when it exits.  Great for testing purposes!
    """

    def __init__(self, broker, output_file=None, subscriptions=tuple(), stats_to_collect = ('count',), **kwargs):
        """

        :param broker:
        :param output_file: if specified, write results to file when exiting
        :param subscriptions: stats for each subscription will be collected separately
        :param stats_to_collect: define which stats should be collected (default is all supported ones)
        :param kwargs:
        """
        super(StatisticsApplication, self).__init__(broker=broker, subscriptions=subscriptions, **kwargs)

        self._out_file = output_file

        if not subscriptions:
            raise ValueError("can't gather any stats as no 'subscriptions' requested!")
        if not stats_to_collect:
            raise ValueError("no statistics requested for collection!")

        # initialize the stats dict to contain only the ones of interest so we don't attempt wrongful operations on data
        # NOTE: when adding new stats, careful to make sure they don't need a deepcopy!
        stats_defaults = dict(count=0)
        try:
            init_stats = {k: stats_defaults[k] for k in stats_to_collect}
        except KeyError as e:
            raise ValueError("unrecognized statistic requested: %s" % e)
        self._stats = {topic: init_stats.copy() for topic in subscriptions}

    def on_event(self, event, topic):
        log.debug("received %s event for processing" % topic)
        self._analyze_event(event, topic)

    def _analyze_event(self, event, topic):
        """
        Helper method to analyze the event and collect stats from it.  Useful for testing instead of directly calling on_event()
        :param event:
        :param topic:
        :return:
        """
        stats = self._stats[topic]

        # collect all the stats possible
        try:
            stats['count'] += 1
        except KeyError:
            pass

    @property
    def stats(self):
        return self._stats

    def get_stats(self, topic, which_stats=None):
        """
        Returns the stats for the requested topic and (optional) statistic (default is a dict with all of them).
        :param topic:
        :param which_stats:
        :return:
        """
        ret = self._stats[topic]
        if which_stats is not None:
            return ret[which_stats]
        return ret

    def write_stats(self, filename):
        """
        Writes the stats (in JSON-serialized dict representation) to the specified file.
        :param filename:
        :return:
        """

        with open(filename, 'w') as f:
            data = json.dumps(self.stats)
            f.write(data)

    def on_stop(self):
        if self._out_file:
            self.write_stats(self._out_file)
        log.warning("Stats gathered: %s" % self.stats)
        super(StatisticsApplication, self).on_stop()