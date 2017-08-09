import unittest
import json
import subprocess


# quit all tests after this long in case they hang
QUIT_TIME = 10
LOG_LEVEL = 'debug'


class TestCoapRemoteSink(unittest.TestCase):
    """
    Run two clients as separate processes: 'client' will generate dummy events and sink them to a RemoteCoapEventSink;
    'server' will receive these events on its CoapServer and gather statistics about the events received.
    The unit test validates that these received event-related statistics match our expectations.
    """

    def test_with_stats(self):
        server_config = """--networks '
CoapServer:
    class: "coap_server.CoapServer"
    events_root: "/events/"
' \
--applications '
StatisticsApp:
    class: "statistics_application.StatisticsApplication"
    subscriptions: ["dummy_event"]
    output_file: "_server_stats.json"
' \
"""

        client_config = """--sensors '
DummySensor:
    class: "dummy.heartbeat_sensor.HeartbeatSensor"
    event_type: "dummy_event"
' \
--event-sinks '
CoapEventSink:
    class: "remote_coap_event_sink.RemoteCoapEventSink"
    topic: "/events/%s"
' \
--applications '
StatisticsApp:
    class: "statistics_application.StatisticsApplication"
    subscriptions: ["dummy_event"]
    output_file: "_client_stats.json"
' \
"""
        # NOTE: to keep output from showing in console and possibly retrieve it later, use:
        # stderr=subprocess.PIPE and then do self.server_client.stderr.read()
        self.server = subprocess.Popen("python -m scale_client --raise-errors --quit-time %d --log-level %s %s" % (QUIT_TIME, LOG_LEVEL, server_config), shell=True)
        self.client = subprocess.Popen("python -m scale_client --raise-errors --quit-time %d --log-level %s %s" % (QUIT_TIME, LOG_LEVEL, client_config), shell=True)

        print "waiting for clients to finish..."
        self.server.wait()
        self.client.wait()
        # print self.server_client.stderr.read()

        with open("_server_stats.json") as f:
            text = f.read().strip()
            data = json.loads(text)
            print "server stats:", data
            server_count = data['dummy_event']['count']

        with open("_client_stats.json") as f:
            text = f.read().strip()
            data = json.loads(text)
            print "client stats:", data
            client_count = data['dummy_event']['count']

        self.assertGreaterEqual(client_count, server_count, "how can server have received more events than the client that made them???")
        self.assertAlmostEqual(server_count, client_count, delta=3,
                               msg="difference between #events on server vs. client exceeded threshold! why so many missing?")


# TODO: we'll test local coap sink later, but probably in a different manner.  This was an attempt to experiment with
# running a unit test with multiple threads/processes (each client needs one) and then inspect the components directly.
# HOWEVER, this will probably be more hassle than it's worth especially since most use cases
# (e.g. mininet/raspi experiments) will require launching a separate process through command line args rather than
# directly constructing a class in python.

# class TestCoapLocal(unittest.TestCase):
#     """
#     Store events in the LocalCoapEventSink and ensure others can read them.
#     """
#
#     def setUp(self):
#         from scale_client.util.defaults import set_logging_config
#         import logging
#         set_logging_config(level=logging.DEBUG)
#
#         ## First create the clients to get a broker
#
#         # This one runs the sink
#         self.server_client = ScaleClient(quit_time=QUIT_TIME)
#         self.server_client.setup_broker()
#         self.server_client.setup_reporter()
#
#         # This one will pull data from it
#         # NOTE: maybe we can't get away with this ...  unclear that we'll be able to run two clients in separate processes: what happens to the socket handles that were opened???
#         self.remote_client = self.server_client
#         # self.remote_client = ScaleClient(quit_time=QUIT_TIME)
#         # self.remote_client.setup_broker()
#         # self.remote_client.setup_reporter()
#
#         ## Now set up the other components
#
#         # Coap parts
#         topic_to_share = "/events/dummy_data"
#         self.coap_sink = LocalCoapEventSink(self.server_client.broker, topic=topic_to_share)
#         self.coap_sensor = CoapSensor(self.remote_client.broker, topic=topic_to_share)
#         # since we cache the server we should only build it once
#         try:
#             self.coap_server = CoapServer(self.server_client.broker)
#         except ValueError:
#             self.coap_server = get_coap_server()
#
#         # Dummy heartbeat sensor to provide data
#         self.dummy_sensor = HeartbeatSensor(broker=self.server_client.broker, event_type="dummy_data")
#
#         # Test event sink to verify that data was received remotely
#         self.test_sink = LogEventSink(broker=self.remote_client.broker)
#
#         # Register with event reporter
#         self.server_client.event_reporter.add_sink(self.coap_sink)
#         self.remote_client.event_reporter.add_sink(self.test_sink)
#
#     def test_remote_sensor(self):
#         print 'should see some events being published by the sensor'
#         self.server_client.run()
#
#     def tearDown(self):
#         print 'sleeping so network ports can be reclaimed...'
#         time.sleep(4)


# TODO: simple unit tests on creating the coap components themselves
# test these classes individually?
# from scale_client.networks.coap_client import CoapClient
# from scale_client.networks.coap_server import CoapServer

if __name__ == '__main__':
    unittest.main()