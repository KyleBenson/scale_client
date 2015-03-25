import time
from circuits import Event
import pprint

class SensedEvent(Event):
    """
    A SensedEvent is the basic piece of data in the whole system.  Various sensors create SensedEvents
    from raw physical phenomena or other SensedEvents.  A SensedEvent mainly consists of just some data
    representing the real-world event, an identifier for what Sensor it came from, and a priority and
    timestamp value.
    """
    def __init__(self, sensor, data, priority, timestamp=None):
        super(SensedEvent, self).__init__()
        # TODO: polymorphic lazy version of this object?
        self.sensor = sensor            # Sensor identifier
        self.priority = priority        # Smaller integer for higher priority

        # we must ensure that the SensedEvent's data follows a convention of being a dict-like object
        try:
            data['value']
        except TypeError:
            data = {"event": "unknown_event_type", "value": data}
        self.data = data                  # Some abstract data that describes the event

        # timestamp defaults to right now
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

    def get_raw_data(self):
        """
        This function tries to intelligently extract just the raw reading from the possibly-nested self.data attribute,
        which may include other information such as units, etc.
        :return: raw data
        """
        data = self.data['value']
        try:
            return data['value']
        except TypeError:
            return data
        except KeyError:
            return data

    def get_type(self):
        """
        This function tries to intelligently extract the type of SensedEvent as a string.
        :return: event type
        """
        return self.data['event']

    def __repr__(self):
        s = "SensedEvent (%s) with value %s" % (self.get_type(), str(self.get_raw_data()))
        s += pprint.pformat(self.data, width=1)
        return s

    def to_json(self):
        import json
        import copy

        map_d = copy.copy(self.data)

        # TODO: map_d["sensor"] = self.sensor
        map_d["timestamp"] = self.timestamp
        map_d["prio_value"] = self.priority
        if map_d["prio_value"] < 4:
            map_d["prio_class"] = "high"
        elif map_d["prio_value"] > 7:
            map_d["prio_class"] = "low"
        else:
            map_d["prio_class"] = "medium"

        return json.dumps({"d": map_d})
