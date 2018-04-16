import unittest

from sensed_event_generator import SensedEventGenerator
from scale_client.core.sensed_event import SensedEvent

# set to False for quicker tests that might not catch some very unlikely errors: we're working with probability distributions!
THOROUGH_TESTING = True

class TestSensedEventGenerator(unittest.TestCase):

    def setUp(self):
        self.gen = SensedEventGenerator()

    def test_bounds(self):
        # time should not be negative or exceed the total_time bound
        # XXX: we run this several times since the total time limit results in fewer samples anyway
        for i in range(100 if THOROUGH_TESTING else 10):
            total_time = 100
            evs = list(self.gen.generate_publications('blah', {'dist': 'norm'}, total_time=total_time))
            self.assertTrue(all(0 < t <= total_time for topic, t, d in evs))
            evs = list(self.gen.generate_publications('blah', {'dist': 'expon'}, total_time=total_time))
            self.assertTrue(all(0 < t <= total_time for topic, t, d in evs))
            # a bit hacky, this will put the actual random variable bounds outside the total_time!
            evs = list(self.gen.generate_publications('blah', {'dist': 'uniform', 'args': [-10, total_time*2]}, total_time=total_time))
            self.assertTrue(all(0 < t <= total_time for topic, t, d in evs))

        # we give explicit bounds for the data size
        evs = list(self.gen.generate_publications('blah', 2, data_size={'dist': 'uniform', 'args': [-10, 100]},
                                                  data_size_bounds=(5, 10), nevents=1000 if THOROUGH_TESTING else 100))
        self.assertTrue(all(5 <= len(d) <= 10 for topic, t, d in evs))

        # validate that the data is sequence #s once converted from string to integer:
        self.assertTrue(all(int(data) == seq for seq, (topic, t, data) in enumerate(evs)))

        # we request MUCH larger data sizes
        evs = list(self.gen.generate_publications('blah', 2, data_size=500, nevents=1000 if THOROUGH_TESTING else 100))
        self.assertTrue(all(len(d) == 500 for topic, t, d in evs))

        # validate that the data is sequence #s once converted from string to integer:
        self.assertTrue(all(int(data) == seq for seq, (topic, t, data) in enumerate(evs)))

    def test_random_seeds(self):
        """Verifies that specifying the same seed for two rounds of publication generation gives the same results;
        different seeds should give different results!"""

        evs1 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 12345}, nevents=10))
        evs2 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 12345}, nevents=10))
        self.assertEqual(evs1, evs2)

        evs3 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 12345}, nevents=10))
        evs4 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 67890}, nevents=10))
        self.assertNotEqual(evs3, evs4)

        # make sure we can leave out the seed
        evs5 = list(self.gen.generate_publications('blah', {'dist': 'norm'}, nevents=1000))
        evs6 = list(self.gen.generate_publications('blah', {'dist': 'norm'}, nevents=1000))
        self.assertNotEqual(evs5, evs6)

        # ensure it works on both fields
        evs1 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 12345}, nevents=10,
                                                   data_size={'dist': 'uniform', 'args': [10, 100], 'seed': 67890}))
        evs2 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 67890}, nevents=10,
                                                   data_size={'dist': 'uniform', 'args': [10, 100], 'seed': 12345}))
        evs3 = list(self.gen.generate_publications('blah', {'dist': 'norm', 'seed': 67890}, nevents=10,
                                                   data_size={'dist': 'uniform', 'args': [10, 100], 'seed': 12345}))
        self.assertNotEqual(evs1, evs2)
        self.assertEqual(evs3, evs2)

    def test_termination(self):

        # total_time termination

        # NOTE: just use periodic events as otherwise we have to mess with seeds and assume the underlying RNG never changes...

        evs = list(self.gen.generate_publications('blah', 5, total_time=100))
        self.assertEqual(len(evs), 20)

        evs = list(self.gen.generate_publications('blah', 5, total_time=5))
        self.assertEqual(len(evs), 1)

        evs = list(self.gen.generate_publications('blah', 3, total_time=5))
        self.assertEqual(len(evs), 1)

        # total events (nevents) termination

        evs = list(self.gen.generate_publications('blah', 3, nevents=5))
        self.assertEqual(len(evs), 5)

        evs = list(self.gen.generate_publications('blah', 3, nevents=1))
        self.assertEqual(len(evs), 1)

        evs = list(self.gen.generate_publications('blah', 3, nevents=0))
        self.assertEqual(len(evs), 0)

        # test both: should be the first!

        evs = list(self.gen.generate_publications('blah', 5, nevents=10, total_time=100))
        self.assertEqual(len(evs), 10)

        evs = list(self.gen.generate_publications('blah', 5, nevents=10, total_time=20))
        self.assertEqual(len(evs), 4)

    def test_get_sensed_events(self):
        # just make sure we don't get errors...
        evs = list(self.gen.generate_sensed_events('blah', {'dist': 'norm', 'seed': 12345}, nevents=1000,
                                                   data_size={'dist': 'uniform', 'args': [10, 100], 'seed': 67890}))
        self.assertTrue(all(isinstance(se, SensedEvent) for se in evs))

        # then check that passing args to get_sensed_events... works
        evs = list(self.gen.generate_sensed_events('blah', {'dist': 'norm', 'seed': 12345}, nevents=1000,
                                                   data_size={'dist': 'uniform', 'args': [10, 100], 'seed': 67890},
                                                   init_time=500, metadata={'blah': 'bob'}))
        self.assertTrue(all(se.timestamp > 500 and se.metadata['blah'] == 'bob' for se in evs))


if __name__ == '__main__':
    unittest.main()
