import json
import os
import subprocess
import unittest

from scale_client.core.client import make_scale_config
from scale_client.networks.util import DEFAULT_COAP_PORT

# quit all tests after this long in case they hang
QUIT_TIME = 10
LOG_LEVEL = 'debug'
# optionally ignore the processes' output (stderr since most output is logging; stdout still prints for quick hacking)
DISPLAY_PROC_OUTPUT = False
# ideally this would only be 1-2, but it does seem like it can go up to 4 fairly often...
TOLERATED_EVENT_COUNT_DIFFERENCE = 4


class TestCoap(unittest.TestCase):
    """
    Basic Coap integration testing by running multiple scale clients in different processes in order to verify
    their proper interactions via coap
    """

    def test_remote_sink(self):
        """
        Run two clients as separate processes:
        'client' will generate dummy events and sink them to a RemoteCoapEventSink;
        'server' will receive these events on its CoapServer;
        both gather statistics about the events seen, which the unit test uses to validate our expectations.
        Also verifies that events received from a remote source are published internally but not sent to an EventSink.
        """

        self.server_output_file = "_server_stats.json"
        self.client_output_file = "_client_stats.json"
        self.zero_expected_sink_output_file = "_zero_sink_stats.json"
        # these will be cleaned up in tearDown
        self.output_files = (self.server_output_file, self.client_output_file, self.zero_expected_sink_output_file)
        self.server_config = make_scale_config(applications=get_stats_app_config(self.server_output_file),
                                               networks=get_coap_server_config(),
                                               sinks=get_stats_sink_config(self.zero_expected_sink_output_file))
        self.client_config = make_scale_config(sensors=get_dummy_sensor_config(), sinks=get_remote_sink_config(),
                                               applications=get_stats_app_config(self.client_output_file))

        self.run_procs(self.server_config, self.client_config)
        server_stats, client_stats, zero_expected_sink_stats = self.read_output_files(self.server_output_file,
                                                                                      self.client_output_file,
                                                                                      self.zero_expected_sink_output_file)
        server_count = server_stats[DEFAULT_EVENT_TYPE]['count']
        client_count = client_stats[DEFAULT_EVENT_TYPE]['count']
        zero_expected_sink_count = zero_expected_sink_stats[DEFAULT_EVENT_TYPE]['count']

        # Check that results are correct
        print "counts:", server_count, "(server app)", zero_expected_sink_count, "(0-expected sink)", client_count, "(client)"
        self.assertGreaterEqual(client_count, server_count, "how can server have received more events than the client that made them???")
        self.assertGreater(server_count, 0, "no events received remotely on server!")
        self.assertGreater(client_count, 0, "no events received locally on client!")
        self.assertAlmostEqual(server_count, client_count, delta=TOLERATED_EVENT_COUNT_DIFFERENCE,
                               msg="difference between #events on server vs. client exceeded threshold of %d!"
                                   " why so many missing? may try running again as this happens sometimes..." %\
                               TOLERATED_EVENT_COUNT_DIFFERENCE)
        expected_events = QUIT_TIME
        self.assertAlmostEqual(expected_events, client_count, delta=TOLERATED_EVENT_COUNT_DIFFERENCE,
                               msg="too few events were published on the client! regression?")
        self.assertEqual(zero_expected_sink_count, 0, "EventSink should not receive remote events!")


    def test_local_sink_remote_observer(self):
        """
        Run two clients as separate processes:
        'server' will generate dummy events and sink them to its CoapServer via a LocalCoapEventSink;
        'client' will observe these events with a CoapSensor;
        both gather statistics about the events seen, which the unit test uses to validate our expectations.
        Also verifies that events received from a remote source are published internally but not sent to an EventSink.
        """

        # TODO: test both polling and observe modes of CoapSensor
        # Could do this by putting most of the logic in the setup/teardown and have two different tests

        self.server_output_file = "_server_stats.json"
        self.client_output_file = "_client_stats.json"
        self.zero_expected_sink_output_file = "_zero_sink_stats.json"

        # these will be cleaned up in tearDown
        self.output_files = (self.server_output_file, self.client_output_file, self.zero_expected_sink_output_file)
        self.server_config = make_scale_config(sensors=get_dummy_sensor_config(),
                                               applications=get_stats_app_config(self.server_output_file),
                                               networks=get_coap_server_config(),
                                               sinks=get_local_sink_config())
        self.client_config = make_scale_config(sensors=get_coap_sensor_config(),
                                               applications=get_stats_app_config(self.client_output_file),
                                               sinks=get_stats_sink_config(self.zero_expected_sink_output_file))

        self.run_procs(self.server_config, self.client_config)
        server_stats, client_stats, zero_expected_sink_stats = self.read_output_files(self.server_output_file,
                                                                                      self.client_output_file,
                                                                                      self.zero_expected_sink_output_file)
        server_count = server_stats[DEFAULT_EVENT_TYPE]['count']
        client_count = client_stats[DEFAULT_EVENT_TYPE]['count']
        zero_expected_sink_count = zero_expected_sink_stats[DEFAULT_EVENT_TYPE]['count']

        # Check that results are correct
        print "counts:", server_count, "(server app)", zero_expected_sink_count, "(0-expected sink)", client_count, "(client)"
        self.assertGreater(server_count, 0, "no events received locally on server!")
        self.assertGreater(client_count, 0, "no events received remotely on client!")
        self.assertGreaterEqual(server_count, client_count, "how can client have received more events than the server that made them???")
        self.assertAlmostEqual(server_count, client_count, delta=TOLERATED_EVENT_COUNT_DIFFERENCE,
                               msg="difference between #events on server vs. client exceeded threshold of %d!"
                                   " why so many missing? may try running again as this happens sometimes..." %\
                               TOLERATED_EVENT_COUNT_DIFFERENCE)
        expected_events = QUIT_TIME
        self.assertAlmostEqual(expected_events, server_count, delta=TOLERATED_EVENT_COUNT_DIFFERENCE,
                               msg="too few events were published on the server! regression?")
        self.assertEqual(zero_expected_sink_count, 0, "EventSink should not receive remote events!")


    def run_procs(self, *configs):
        """
        Runs the scale client processes for the configs and waits for them to complete
        :param configs: list of config strings for determining which components to run on the scale client processes
        :return:
        """
        procs = []
        for cfg in configs:
             procs.append(run_scale_client_process(cfg))

        print "waiting for processes to finish (should only take %d seconds)..." % QUIT_TIME
        for p in procs:
            p.wait()
            # if you piped the proc output, can still print it out after it's finished using:
            # print p.stderr.read()


    def read_output_files(self, *files):
        """Read files output by the StatisticsApplication modules (JSON files)"""
        outputs = []
        for _file in files:
            with open(_file) as f:
                text = f.read().strip()
                data = json.loads(text)
                outputs.append(data)

        return outputs


    def tearDown(self):
        try:
            for f in self.output_files:
                os.remove(f)
        except AttributeError:
            pass

##### further tests to include:
# TODO: verify that remote events aren't reported to sinks
# TODO: test with multiple clients
# TODO: simple unit tests on creating the coap components themselves
# TODO: test REST API itself directly instead of indirectly through the events API
# test these classes individually?
# from scale_client.networks.coap_client import CoapClient
# from scale_client.networks.coap_server import CoapServer


############    CONFIGURATIONS      ###############


# combine these raw YAML configs as needed for the various test cases
# NOTE: we wrap them in single quotes to keep newlines from ending the commands
DEFAULT_EVENT_ROOT = "/events/"
DEFAULT_EVENT_TOPIC = DEFAULT_EVENT_ROOT + '%s'
DEFAULT_EVENT_TYPE = "dummy_event"

def get_coap_server_config(port=DEFAULT_COAP_PORT, event_root=DEFAULT_EVENT_ROOT):
    return """'
CoapServer:
    class: "coap_server.CoapServer"
    events_root: %s
    port: %d
'""" % (event_root, port)

def get_remote_sink_config(topic=DEFAULT_EVENT_TOPIC):
    return """'
RemoteCoapEventSink:
    class: "remote_coap_event_sink.RemoteCoapEventSink"
    topic: %s
'""" % topic

def get_local_sink_config(topic=DEFAULT_EVENT_TOPIC):
    return """'
LocalCoapEventSink:
    class: "local_coap_event_sink.LocalCoapEventSink"
    topic: %s
'""" % topic

def get_coap_sensor_config(port=DEFAULT_COAP_PORT, timeout=4, polling_interval=None,
                           topic=DEFAULT_EVENT_TOPIC % DEFAULT_EVENT_TYPE):
    """
    Configures a CoapSensor with the given parameters: it will use observe if polling_interval not set.
    :param port:
    :param timeout: NOTE: we use a short timeout since we're starting it at the same time as the other client's server.
    This ensures that we'll retry an observe quickly since the first time the data usually isn't available yet.
    :param polling_interval: if specified, sets the sample_interval to the given number of seconds
    :param topic: topic to observe
    :return:
    """
    cfg = """'
CoapSensor:
    class: "network.coap_sensor.CoapSensor"
    topic: %s
    timeout: %d
    port: %d
'""" % (topic, timeout, port)
    if polling_interval:
        cfg += "'use_polling: True\nsample_interval: %d'" % polling_interval
    return cfg

def get_dummy_sensor_config(event_type=DEFAULT_EVENT_TYPE):
    return """'
DummySensor:
    class: "dummy.heartbeat_sensor.HeartbeatSensor"
    event_type: %s
    sample_interval: 1
'""" % event_type

def get_stats_app_config(output_file, subscriptions=[DEFAULT_EVENT_TYPE]):
    return """'
StatisticsApp:
    class: "statistics_application.StatisticsApplication"
    subscriptions: %s
    output_file: %s
'""" % (subscriptions, output_file)

def get_stats_sink_config(output_file, subscriptions=[DEFAULT_EVENT_TYPE]):
    return """'
StatisticsSink:
    class: "statistics_event_sink.StatisticsEventSink"
    subscriptions: %s
    output_file: %s
'""" % (subscriptions, output_file)

# TODO: refactor run_scale_client_process, and the self.run_procs/read_output/tearDown into either tests/util.py and/or a base class for unittests
# the get_x_config functions were kind of silly: could mostly replace them with json.dumps(dict(name=StatsSink, **kwargs))

# TODO: configurable quits, logs, etc.?
def run_scale_client_process(config):
    """Run the scale client in a subprocess"""
    # NOTE: to keep output from showing in console and possibly retrieve it later, use:
    #  and then do self.server_client.stderr.read()
    if DISPLAY_PROC_OUTPUT:
        return subprocess.Popen("python -m scale_client --raise-errors --quit-time %d --log-level %s %s" %\
                                (QUIT_TIME, LOG_LEVEL, config), shell=True)
    else:
        return subprocess.Popen("python -m scale_client --raise-errors --quit-time %d --log-level %s %s" %\
                                (QUIT_TIME, LOG_LEVEL, config), shell=True, stderr=subprocess.PIPE)


if __name__ == '__main__':
    unittest.main()