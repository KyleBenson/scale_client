import unittest

from scale_client.applications.event_storing_application import EventStoringApplication
from scale_client.applications.statistics_application import StatisticsApplication
from scale_client.sensors.dummy.random_virtual_sensor import RandomVirtualSensor
# for testing RVS we need to run a whole client
from scale_client.core.client import ScaleClient, configure_logging
from scale_client.core.sensed_event import SensedEvent


class TestRandomVirtualSensor(unittest.TestCase):
    """
    Test that our event-generation works, especially given the async nature of a RandomVS.
    """

    def setUp(self):
        # to test this, we need to build a client and have a stats app to subscribe
        self.quit_time = 6
        args = ScaleClient.parse_args()  # default args
        args.log_level = 'debug'
        configure_logging(args)

    def test_nevents(self):

        # FIRST TEST: basic periodic publishing with limited # events
        # NOTE: make sure you bound the number of events generated or the SCALE client won't stop running!
        gen_cfg = dict(topic='fire', publication_period=.5, nevents=10)

        client = ScaleClient(quit_time=self.quit_time, raise_errors=True)
        broker = client.setup_broker()
        pub = RandomVirtualSensor(broker, event_generator=gen_cfg)
        stats_sub = StatisticsApplication(broker, subscriptions=('fire', 'ice'))
        events_sub = EventStoringApplication(broker, subscriptions=('fire', 'ice'))

        # get time of start and end; ensure all events have increasing timestamps between these values
        start_time = SensedEvent.get_timestamp()
        client.run()
        end_time = SensedEvent.get_timestamp()

        # verify # events generated
        self.assertEqual(stats_sub.get_stats('fire', 'count'), 10)

        for ev in events_sub.events:
            self.assertLess(start_time, ev.timestamp)
            self.assertLess(ev.timestamp, end_time)

        ## EDGE CASE: no events generated with 0 total events

        gen_cfg = dict(topic='fire', publication_period=.5, nevents=0)

        client = ScaleClient(quit_time=self.quit_time, raise_errors=True)
        broker = client.setup_broker()
        pub = RandomVirtualSensor(broker, event_generator=gen_cfg)
        stats_sub = StatisticsApplication(broker, subscriptions=('fire', 'ice'))
        client.run()

        # verify no events generated
        self.assertEqual(stats_sub.get_stats('fire', 'count'), 0)

    def test_total_time(self):

        # SECOND TEST: limited time duration of published events
        duration = 3
        gen_cfg = dict(topic='fire', publication_period=.5, total_time=duration)

        client = ScaleClient(quit_time=self.quit_time, raise_errors=True)
        broker = client.setup_broker()
        pub = RandomVirtualSensor(broker, event_generator=gen_cfg)
        stats_sub = StatisticsApplication(broker, subscriptions=('fire', 'ice'))
        events_sub = EventStoringApplication(broker, subscriptions=('fire', 'ice'))

        # get time of start and end; ensure all events have increasing timestamps between these values
        start_time = SensedEvent.get_timestamp()
        client.run()

        # verify SOME events generated
        self.assertGreater(stats_sub.get_stats('fire', 'count'), 3)

        # Verify times are as expected
        for ev in events_sub.events:
            self.assertLess(start_time, ev.timestamp)
            # give a little lag time for the last event
            self.assertLess(ev.timestamp, start_time + duration + 0.2)

        ## EDGE CASE: no events generated with 0 time covered

        gen_cfg = dict(topic='fire', publication_period=.5, total_time=0)

        client = ScaleClient(quit_time=self.quit_time, raise_errors=True)
        broker = client.setup_broker()
        pub = RandomVirtualSensor(broker, event_generator=gen_cfg)
        stats_sub = StatisticsApplication(broker, subscriptions=('fire', 'ice'))
        client.run()

        # verify no events generated
        self.assertEqual(stats_sub.get_stats('fire', 'count'), 0)

    def test_async(self):

        # THIRD TEST: asynchronous events, which we verify worked by setting appropriate bounds on pub times
        duration = 5
        gen_cfg = dict(topic='fire', publication_period=dict(dist='exp', args=(0.5,), lbound=0.5, ubound=1), total_time=duration)

        client = ScaleClient(quit_time=duration + 1, raise_errors=True)
        broker = client.setup_broker()
        pub = RandomVirtualSensor(broker, event_generator=gen_cfg)
        stats_sub = StatisticsApplication(broker, subscriptions=('fire', 'ice'))
        events_sub = EventStoringApplication(broker, subscriptions=('fire', 'ice'))

        # get time of start and end; ensure all events have increasing timestamps between these values
        start_time = SensedEvent.get_timestamp()
        client.run()

        # verify expected # events generated
        self.assertGreaterEqual(stats_sub.get_stats('fire', 'count'), 4)
        self.assertLessEqual(stats_sub.get_stats('fire', 'count'), 11)

        # Verify times are as expected
        # ENHANCE: how to do this automatically?
        print "MANUALLY verify these pub times look async:"
        ev_times = [ev.timestamp - start_time for ev in events_sub.events]
        for i in range(len(ev_times))[1:]:
            ev_times[i] -= ev_times[i - 1]
        print ev_times

        last_time = events_sub.events[0].timestamp
        for ev in events_sub.events[1:]:
            self.assertLess(start_time, ev.timestamp)
            # give a little lag time for the last event
            self.assertLess(ev.timestamp, start_time + duration + 0.2)
            # ensure time diff is within our bounds (roughly)
            this_time = ev.timestamp
            self.assertLess(this_time - last_time, 1.1)
            self.assertGreater(this_time - last_time, 0.5)
            last_time = this_time


if __name__ == '__main__':
    unittest.main()
