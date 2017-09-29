import json
import time
# CIRCUITS-SPECIFIC:
from circuits import Event
import pprint

from copy import deepcopy

from scale_client.util import uri

import logging
log = logging.getLogger(__name__)


class SensedEvent(Event):
    """
    A SensedEvent is the basic piece of data in the whole system.  Various sensors create SensedEvents
    from raw physical phenomena or other SensedEvents.  A SensedEvent mainly consists of just some data
    representing the real-world event, an identifier for what data source (Application or str)
     it came from, a string representing the event type, some required canonical metadata (e.g. priority, timestamp),
    some optional fields (e.g. condition on which the event happened, location, units the raw value is in,
    schema version), and a generic dict representing additional metadata.
    """

    DEFAULT_PRIORITY = 10
    # TODO: actually write and register a schema?
    DEFAULT_SCHEMA = "www.schema.org/scale/2.0/sensed_event"

    def __init__(self, data, source, priority=None, event_type="unknown_event_type",
                 timestamp=None, condition=None, location=None, units=None,
                 metadata=None, schema=DEFAULT_SCHEMA, **metadata_additional_kwargs):
        """
        :param source: a URI representing the source of this event e.g.
        a VirtualSensor that initially published it, the remote device it came from, etc.
        :type source: basestring
        :param data: raw event data
        :param priority: int in range 0-10 with 0 being highest priority
        :param event_type: short human-readable type/name/topic of event e.g. temperature, door_open, ping, etc.
        :param timestamp: expressed as Unix epoch; defaults to now
        :param condition: an optional encoded condition on which this event was raised (it's a conjunction)
        e.g. {'threshold': {'operator': '>', 'value': 24.0}}
        OR {'event': PreviousSensedEvent, 'state_transition': [States.OLD, States.NEW]}
        :param location: optional location of event e.g. lat-lon in a dict or '3rd floor' or ...
        :param units: optional units the reading is in e.g. 'celsius' or 'raw_analog'
        :param metadata: optional dict of misc. metadata about this event
        :param schema: URI for the schema of this event (default is latest SCALE events schema: see method signature)
        :param metadata_additional_kwargs: any unrecognized args will be added into the metadata dict
        """

        # CIRCUITS-SPECIFIC: in order for callbacks registered via Application.subscribe to work,
        # their parameters must match those used to create the Event being fired.  Hence, we need
        # to pass the SensedEvent itself into Event's constructor in order to get the SensedEvent
        # passed into those callbacks.
        super(SensedEvent, self).__init__(self)

        self.source = source
        self.data = data

        if priority is None:
            priority = self.__class__.DEFAULT_PRIORITY
        if type(priority) != type(0):
            raise TypeError("event priority should be an integer in range 0-10!")
        self.priority = priority        # Smaller integer for higher priority

        # These are nullable or have explicit defaults
        self.event_type = event_type
        self.condition = condition
        self.location = location
        self.units = units
        self.schema = schema
        # we want to be able to add metadata later if none is given
        self.metadata = metadata if metadata is not None else {}
        if metadata_additional_kwargs:
            self.metadata.update(metadata_additional_kwargs)

        # timestamp defaults to right now
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

    @property
    def is_local(self):
        """
        Determines whether this event was created by a local entity.  Currently, this is based
        solely on the source URI, but may include some additional context later...
        NOTE: a simple string source e.g. "temperature" will be assumed to be a local event
        due to the assumption that remotely-gathered events will be tagged with their network source!
        :return:
        """
        return not uri.is_remote_uri(self.source)

    ## These properties are mostly maintained as convenience accessors to the event's fields,
    # some of which are for the purpose of backwards compatibility or getting default values.
    @property
    def topic(self):
        return self.event_type
    @property
    def sensor(self):
        raise DeprecationWarning("a SensedEvent's sensor or device field is now referred to as source and should be a proper URI!")

    def __eq__(self, other):
        """
        Simple equality test mostly just used for testing purposes.
        :param other:
        :return:
        """
        # TODO: since a source could be a remote entity, we can't just assume we have the same source object
        # but should rather consider the possibility that we have two different representations of the same source.
        same_source = self.source == other.source
        # NOTE: we don't need the schema to be the same as it might have different versions but be the same true data,
        # we can't assume the metadata will be identical since some apps may add arbitrary fields during processing,
        # and we currently assume the priority will be identical but may wish to change that later since
        # some app may declare this event as having a higher/lower priority than its default value for example.
        # TODO: how to handle condition?

        return same_source and self.data == other.data and self.timestamp == other.timestamp and\
               self.event_type == other.event_type and self.priority == other.priority and\
               self.units == other.units and self.location == other.location

    def __repr__(self):
        s = "SensedEvent (value=%s, type=%s, src=%s, prio=%s, time=%s)" %\
            (str(self.data), self.event_type, self.source, self.priority, self.timestamp)
        # s+= "units=%s, location=%s" % (self.units, self.location)
        return s

    def pretty_print(self):
        s = pprint.pformat(self.to_map(), width=1)
        return s

    #### Below this is all related to encoding/decoding
    # This should probably be moved to an encoder class in the future...

    def to_map(self, exclude_fields=tuple()):
        """
        Converts the SensedEvent to a dict representation, excluding the specified fields if any.
        :param exclude_fields:
        :return:
        """
        ret = dict(timestamp=self.timestamp, schema=self.schema)
        # FUTURE: SCALE 3.0 schema
        # ENHANCE: would be great to have each field of the event get registered e.g. with a decorator so they can
        #     automatically be filled in, parsed, set to be optional, etc...
        # event_type=self.event_type,
        # priority=self.priority,
        # data=self.data
        # source=data_source

        # Optional fields
        if self.location:
            ret["location"] = self.location
        if self.condition:
            ret["condition"] = self._encode_condition(self.condition)
        if self.units:
            ret["units"] = self.units
        # FUTURE: metadata

        # XXX: old SCALE 1.0 schema
        # TODO: this should be handled by a helper function since the assigned class should be configurable by client
        if 0 <= self.priority < 4:
            prio_class = "high"
        elif 7 <= self.priority <= 10:
            prio_class = "low"
        elif 4 <= self.priority < 7:
            prio_class = "medium"
        else:
            raise ValueError("priority value not in range [0,10]!  Can't assign a priority class..")

        old_schema_dict = dict(value=self.data, event=self.event_type, device=self.source,
                               prio_value=self.priority, prio_class=prio_class)

        # Optional fields
        if self.metadata:
            old_schema_dict["misc"] = deepcopy(self.metadata)

        ret.update(old_schema_dict)

        # now exclude the requested fields
        ret = {k: v for k,v in ret.items() if k not in exclude_fields}

        ret = {'d': ret}

        return ret

    # TODO: these helpers should definitely not be in this class since it creates a circular dependency,
    # which we can escape since we don't explicitly do a type cast...
    def _encode_condition(self, condition=None):
        """
        Encodes the event condition, expected to be a dict, as a map containing only JSON-serializable objects
        :param condition: by default we use self.condition
        :return:
        """
        if condition is None:
            condition = self.condition

        assert isinstance(condition, dict), "dict-based conditions are the only ones currently supported!"

        if "event" in condition or "events" in condition:
            # TODO: we'll need to implement some sort of unique ID for each event to properly deserialize
            # an event at the other end of the wire...
            log.warning("encoding conditions referring to other events not yet fully supported! "
                        "For now, we simply dump the event(s) to string(s)...")
            if 'event' in condition:
                condition['event'] = str(condition['event'])
            else:
                condition['events'] = [str(e) for e in condition['events']]

        return condition

    @classmethod
    def from_map(cls, map_data):
        """
        Creates a SensedEvent from a simple map of that events' attributes as per the SCALE event schema.
        NOTE: we currently expect the input map to be in SCALE 1.0 format;
        in the future will accept different schemas for translation.

        :param map_data:
        :type map_data: dict
        :raises ValueError: if unable to properly parse the map data
        :rtype: SensedEvent
        """

        # NOTE: most of the work being done here is for backwards compatibility...
        # In the future, we'll try to intelligently extract the schema and use that to determine further work

        # Make a copy so we don't alter the passed in data!
        map_data = deepcopy(map_data)

        # XXX: try removing the 'd' from the outside if it's there
        try:
            map_data = map_data['d']
        except KeyError:
            pass

        # Ignore the prio_class as it'll get set automatically during serialization later...
        map_data.pop('prio_class', None)
        try:
            source = map_data.pop('device')
        except KeyError:
            #map_data.pop('source')
            raise NotImplementedError("can't parse SensedEvent with no source/device: %s" % map_data)

        # XXX: backwards compatibility
        _scale_schemas_1_to_3 = dict(event="event_type", value="data", prio_value="priority")
        for k,v in _scale_schemas_1_to_3.items():
            try:
                map_data[v] = map_data.pop(k)
            except KeyError:
                pass

        # TODO: handle timestamps in formats other than double/float
        return cls(source=source, **map_data)

    def to_json(self, exclude_fields=tuple(), no_whitespace=False):
        """
        Encodes the SensedEvent as a JSON string, excluding the specified fields if any.
        :param exclude_fields:
        :param no_whitespace: if specified as True, will eliminate whitespace in the encoding
        :return:
        """
        as_map = self.to_map(exclude_fields=exclude_fields)
        try:
            return json.dumps(as_map, separators=(',',':') if no_whitespace else None)
        except (TypeError, ValueError) as e:
            log.error("Problem jsonifying SensedEvent map: %s" % as_map)
            raise

    @classmethod
    def from_json(cls, json_data):
        """
        Creates a SensedEvent from a raw JSON-encoded string
        :param json_data:
        :raises ValueError: if unable to properly parse either JSON or the map data
        :return:
        """

        ev_map = json.loads(json_data)
        return cls.from_map(ev_map)
