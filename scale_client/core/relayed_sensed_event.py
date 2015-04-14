import time
from circuits import Event
import pprint

class RelayedSensedEvent(Event):
    """
    A RelayedSensedEvent is used to reconstruct SensedEvent class from a relayed sensed event json string
    that the node rececievs from its neighbors. A ReplaySensedEvent consists original data of a SensedEvent
    (the real-world event, an identifier for what Sensor it came from, and a priority and timestamp value), 
    a tag to indicate it is from a neighbor node and a tag to indicate if it is needed to submit to MQTT server 
    """
    def __init__(self, relayed_sensed_event_string):
        super(RelayedSensedEvent, self).__init__()
        
        relayed_sensed_event = self.decode_relayed_sensed_event(relayed_sensed_event_string)
        if relayed_sensed_event:
            self.sensor = relayed_sensed_event['sensor']
            self.priority = relayed_sensed_event['priority']
            self.data = relayed_sensed_event['data']
            self.timestamp = relayed_sensed_event['timestamp']
            self.source = relayed_sensed_event['source']
            self.published = relayed_sensed_event['published']
        else:
            return False


    def decode_relayed_sensed_event(self, relayed_sensed_event_string):
        results = {}

        try:
            relayed_sensed_event = json.load(relayed_sensed_event_string)
            try:
                sensed_event = relayed_sensed_event['sensed_event']
                results['sensor'] = sensed_event['d']['event']
                results['data'] = sensed_event['d']['value']
                results['priority'] = sensed_event['d']['prio_value']
                results['timestamp'] = sensed_event['d']['timestamp']
                results['source'] = relayed_sensed_event['sensor']
                results['published'] = relayed_sensed_event['published']
            except:
                log.info('Received an invalid relayedSensedEvent:' + relayed_sensed_event_string)
                return False
        except:
            log.info('Received an invalid relayedSensedEvent:' + relayed_sensed_event_string)
            return False
        return results

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
