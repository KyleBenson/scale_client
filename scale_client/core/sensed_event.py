import time


class SensedEvent:
    """
    A SensedEvent is the basic piece of data in the whole system.  Various sensors create SensedEvents
    from raw physical phenomena or other SensedEvents.  A SensedEvent mainly consists of just some data
    representing the real-world event, an identifier for what Sensor it came from, and a priority and
    timestamp value.
    """
    def __init__(self, sensor, data, priority, timestamp=None):
        # TODO: polymorphic lazy version of this object?
        self.sensor = sensor            # Sensor identifier
        self.data = data                  # Some abstract data that describes the event
        self.priority = priority        # Smaller integer for higher priority
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

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
