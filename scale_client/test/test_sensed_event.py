import unittest
import json

from scale_client.core.sensed_event import SensedEvent

class TestSensedEvent(unittest.TestCase):
    """
    Test Scale client SensedEvent class for data manipulation, encoding, and decoding.
    This should be used for testing different schema versions.
    """

    def setUp(self):
        self.event = SensedEvent(data=10, source="temp0", event_type="temperature")
        self.minimal_event = SensedEvent(data=10, source="temp0")

    def test_basic_json_encoding(self):
        """
        Tests whether SensedEvent encoding/decoding works as expected.
        :return:
        """
        encoded = self.event.to_json()
        decoded = SensedEvent.from_json(encoded)
        self.assertEqual(self.event, decoded, "encoding then decoding an event should give an essentially identical one back! have: %s and %s" % (self.event, decoded))

    def test_json_encoding_excluded_fields(self):
        """
        Tests whether we can correctly encode a SensedEvent with the exclude_fields option and then correctly decode
        it back.
        :return:
        """

        encoded = self.event.to_json(exclude_fields=('schema', 'condition', 'misc', 'prio_value', 'prio_class'))
        decoded = SensedEvent.from_json(encoded)
        self.assertEqual(self.event, decoded, "encoding then decoding an event should give an essentially identical one back! have: %s and %s" % (self.event, decoded))

        # Now verify that excluding these fields at least allows us to decode the resulting encoded event, even though
        # we KNOW that they will not be truly equal.
        encoded = self.event.to_json(exclude_fields=('timestamp', 'event_type'))
        decoded = SensedEvent.from_json(encoded)  # should not raise error

        # Last, verify that excluding these fields DOES cause an error!
        encoded = self.event.to_json(exclude_fields=('device',))
        with self.assertRaises(NotImplementedError):
            SensedEvent.from_json(encoded)
        encoded = self.event.to_json(exclude_fields=('value',))
        with self.assertRaises(TypeError):
            SensedEvent.from_json(encoded)

    def test_schema_versions(self):
        """
        Tests whether events formatted from different schema versions are compatible with the current data model.
        :return:
        """
        source_device = "scale-local:scale/devices/temperature"
        v1_map = {"d" :
            {"event" : "temperature",
             "value" : 55.5,
             "units" : "celsius",
             "timestamp" : 12345678,
             "device" : source_device,
             "location" : {"lat" : 33.3, "lon" : "-71"},
             "condition" : {"threshold" : {"operator" : ">", "value" : "95"}},
             "prio_class":  "high",
             "prio_value": 2,
             "schema" : "www.schema.org/scale_sensors.1.0.whatever",
            }
           }

        v1_event = SensedEvent.from_map(v1_map)
        self.assertEqual(v1_event.event_type, 'temperature')
        self.assertEqual(v1_event.data, 55.5)
        self.assertEqual(v1_event.priority, 2)
        self.assertEqual(v1_event.source, source_device)

        # Now the other way around: dumping to a map, first by looking at JSON encoding...
        v1_json = json.dumps(v1_map, sort_keys=True)
        manual_v1_json = json.dumps(json.loads(v1_event.to_json()), sort_keys=True)
        self.assertEqual(manual_v1_json, v1_json)

        new_v1_map = v1_event.to_map()
        self.assertEqual(v1_map, new_v1_map, "making into v1.0 schema map didn't produce identical dict: %s" % new_v1_map)

    def test_source(self):
        """
        Tests the special field "source" that be a plain string or URI representing a
        VirtualSensor, DeviceDescriptor, etc... We especially want to make sure that simple
        strings or None are handled well.
        :return:
        """

        # TODO: eventually look up objects by URI in order to determine if they refer to the same one?
        # e.g. we should be able to have a remote device source that refers to a local one of ours be equal...
        pass

    def test_defaults(self):
        """
        Tests whether creating a SensedEvent with minimum # arguments causes unexpected errors
        or leads to a state that will later cause Exceptions to be raised when manipulating the event.
        :return:
        """
        ev = SensedEvent.from_json(self.minimal_event.to_json())
        self.assertEqual(ev, self.minimal_event)

        # Should be able to specify None values for the data (unary event) or source (anonymous event?)
        ev = SensedEvent(data=1, source=None)
        self.assertEqual(SensedEvent.from_json(ev.to_json()), ev)
        ev = SensedEvent(data=None, source='temperature')
        self.assertEqual(SensedEvent.from_json(ev.to_json()), ev)

    def test_is_local(self):
        """
        Tests whether we can properly determine whether a SensedEvent came from our local node or not.
        :return:
        """

        self.assertTrue(self.minimal_event.is_local, "simple string source should be considered local!")
        self.assertFalse(SensedEvent(data=1, source="coap://1.1.1.1/scale/events/temp").is_local,
                         "event from coap source is not local!")


if __name__ == '__main__':
    unittest.main()