import logging
log = logging.getLogger(__name__)

from scale_client.core.sensed_event import SensedEvent

import pandas as pd
import json

DEFAULT_TIMEZONE='America/Los_Angeles'


class ParsedSensedEvents(pd.DataFrame):
    """
    Parses the SensedEvent output file from a SCALE client app and stores it in a pandas.DataFrame
    for later manipulation and aggregation with the other client outputs.

    NOTE: any columns with labels matching 'time*' will be converted to pandas.Timestamp with the expectation that
    they're in Unix epoch format!
    """

    def __init__(self, data, timezone=DEFAULT_TIMEZONE, **kwargs):
        """
        Parses the given data into a dict of events recorded by the client
         and passes the resulting data into a pandas.DataFrame with additional columns specified by kwargs,
        which can include e.g. experimental treatments, host IP address, etc.

        :param data: raw string containing JSON object-like data e.g. nested dicts/lists
        :type data: str
        :param timezone: the timezone to use for converting time columns (default='America/Los_Angeles'); set to None to disable conversion
        :param kwargs: additional static values for columns to distinguish this group of events from others
            e.g. host_id, host_ip
        """
        # NOTE: can't save any attributes until after we run super constructor!

        data = self.parse_data(data, **kwargs)

        # sub-classes may extract the column data in different ways depending on the output format
        columns = self.extract_columns(data)
        columns.update(kwargs)

        self.convert_columns(columns, timezone=timezone)

        super(ParsedSensedEvents, self).__init__(columns)

    def parse_data(self, data, **params):
        """Override this to parse the raw data string using a format other than JSON.  params is ignored by default,
        but corresponds to the kwargs in the constructor."""
        return json.loads(data)

    def extract_columns(self, data, parse_metadata=True):
        """
        Extracts the important columns from the given list of SensedEvents
        :param data:
        :type data: list[dict]
        :param parse_metadata: if True (default), include columns for the metadata
        :return:
        """

        # QUESTION: how to handle empty results???
        events = [SensedEvent.from_map(e) for e in data]

        cols = {'topic': [ev.topic for ev in events],
                'time_sent': [ev.timestamp for ev in events],
                # TODO: might not even want this? what to do with it? the 'scale-local:/' part makes it less useful...
                'source': [ev.source for ev in events],
                'value': [ev.data for ev in events],
                }

        # Include the metadata in case it has something valuable for us.
        # We have to gather up all unique keys first to ensure each row has all the needed columns so they line up.
        metadata_keys = set()
        for ev in events:
            for k in ev.metadata:
                metadata_keys.add(k)
        cols.update({
            k: [ev.metadata.get(k) for ev in events] for k in metadata_keys
        })

        return cols

    def convert_columns(self, columns, timezone=None):
        """
        Converts the columns to more specific pandas data types: this is where we convert time columns.
        :param columns:
        :param timezone: the timezone info to use; to disable this conversion set it to None
        """
        for k, val in columns.items():
            # XXX: any columns starting with 'time' should be converted to pandas.Timestamp!
            if k.startswith('time') and timezone:
                columns[k] = pd.to_datetime(val, unit='s')
                columns[k].tz = timezone
            # TODO: figure out how to take a single value and share it through all rows as a category when it's just a string.
            # BUT: we can't have the values of a category be null so how to do this with messages that never arrive?
            # XXX: basically everything else that isn't numeric is a category
            # elif isinstance(k, basestring):
            #     columns[k] = pd.Series(val, dtype='category')

        return columns

    def rename_columns(self, **map):
        """Renames the columns from key -> value for key, value in map"""
        self.rename(columns=map, inplace=True)
