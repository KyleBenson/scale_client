#!/usr/bin/python
import sys
import yaml
import yaml.parser
import logging
import argparse
import os

from device_descriptor import DeviceDescriptor
from event_reporter import EventReporter
from application import Application
from broker import Broker


class ScaleClient(object):
    """This class parses a configuration file and subsequently creates, configures, and manages each component of the
    overall Scale Client software.
    """
    def __init__(self, quit_time=None):
        super(ScaleClient, self).__init__()

        self._quit_time = quit_time

        self.__broker = None
        self.__reporter = None
        self.__sensors = []
        self.__applications = None

    def setup_reporter(self, cfg):

        if self.__broker is None:
            self.setup_broker(cfg)

        self.__reporter = EventReporter(self.__broker)

    def setup_broker(self, cfg=None):
        """
        Currently only creates a dummy Broker object for registering Applications to.

        :param cfg:
        :return:
        """
        self.__broker = Broker()

    def run(self):
        """Currently just loop forever to allow the other threads to do their work."""

        # HACK: create a dummy app that just calls Broker.stop() at the requested quit_time.
        # We need to do it in an app like this to get the self variables bound in correctly.
        # This is circuits-specific!
        if self._quit_time is not None:
            class QuitApp(Application):
                def _quitter(self):
                    log.info("Stopping client...")
                    self._broker.stop()

            quit_app = QuitApp(self.__broker)
            quit_app.timed_call(self._quit_time, QuitApp._quitter)

        self.__broker.run()

    def setup_components(self, configs, package_name, human_readable, helper_fun=None, *args):
        """
        Iterate over each component configuration in configs, import the specified class
        (possibly using package_name as the root for the import statement), and then call
        helper_fun with the class and requested configuration to finish its setup.  If
        helper_fun isn't specified, the default simply calls the class's constructor
        with the given arguments parsed from the configuration.
        :param configs:
        :param package_name:
        :param human_readable: plain text short name of what component type this is e.g. network, sensor, etc.
        :param helper_fun: responsible for creating the component in question and doing any bookkeeping
        :param args: these args will be passed to helper_fun
        :return: list of constructed classes
        """

        if helper_fun is None:
            def helper_fun(_class, broker, **kwargs):
                return _class(broker, *args, **kwargs)

        results = []

        for cfg in configs:
            # need to get class definition to call constructor
            if 'class' not in cfg:
                log.warn("Skipping %s config with no class definition: %s" % (human_readable, cfg))
                continue

            try:
                cls_name = cfg['class'] if package_name in cfg['class']\
                    else '.'.join([package_name, cfg['class']])
                cls = _get_class_by_name(cls_name)

                # copy config s so we can tweak it as necessary to expose only correct kwargs
                new_config = cfg.copy()
                new_config.pop('class')

                res = helper_fun(cls, self.__broker, *args, **new_config)
                results.append(res)
                log.info("%s created from config: %s" % (human_readable, cfg))

            except ImportError as e:
                log.error("ImportError (%s) while creating %s class: %s\n"
                          "Did you remember to put the repository in your PYTHONPATH???" % (e, human_readable, cfg))
            except Exception as e:
                log.error("Unexpected error while creating %s class: %s\nError: %s" % (human_readable, cfg, e))

        return results


    @classmethod
    def build_from_configuration_parameters(cls, config_filename, args=None):
        """
        Builds an instance using the (optionally) specified configuration file.  If any args are specified
        (e.g. from parse_args()), they may overwrite the configurations in the file.  However,
        such args that create sensors, apps, etc. will just be interpreted as additional
        components being configured: IT'S UP TO YOU to ensure there aren't conflicts!
        If config_filename is None, we just build using the specified args.
        :param config_filename:
        :param args:
        :return:
        """

        # XXX: in case the user forgets to specify a device name,
        # this will help auto-generate unique ones in a sequence.
        global __scale_client_n_sensors_added__
        __scale_client_n_sensors_added__ = 0

        if config_filename is None and args is None:
            raise ValueError("can't build from configuration parameters when both filename and args are None!")

        # Dummy config dict in case no config file
        cfg = {'eventsinks': [], 'sensors': [], 'applications': [], 'networks': []}

        if config_filename is not None:
            try:
                log.info("Reading config file: %s" % config_filename)
                with open(config_filename) as cfile:
                    cfg = yaml.load(cfile)
                    # lower-case all top-level headings to tolerate different capitalizations
                    cfg = {k.lower(): v for k, v in cfg.items()}

            except IOError as e:
                log.error("Error reading config file: %s" % e)
                exit(1)

        # Helper functions for actual config file parsing and handling below.
        def __make_sensor(_class, broker, **config):
            global __scale_client_n_sensors_added__
            dev_name = config.get("dev_name", "vs%i" % __scale_client_n_sensors_added__)
            config.pop('dev_name', dev_name)
            __scale_client_n_sensors_added__ += 1
            return _class(broker, device=DeviceDescriptor(dev_name), **config)

        def __make_event_sink(_class, broker, event_reporter, **config):
            res = _class(broker, **config)
            event_reporter.add_sink(res)
            return res

        def __join_configs_with_args(configs, relevant_args):
            try:
                configs = [c.values()[0] for c in configs]
            except Exception as e:
                raise ValueError("problem (error=%s) extracting configurations from configs: %s" % (e, configs))

            try:
                configs.extend([yaml.load(a) for a in relevant_args])
            except yaml.parser.ParserError as e:
                raise ValueError("error parsing manual configuration: %s\nError:%s" % (relevant_args, e))

            return configs

        ### BEGIN ACTUAL CONFIG FILE USAGE
        # We call appropriate handlers for each section in the appropriate order,
        # starting by getting any relevant command line parameters to create the client.

        client = cls(quit_time=args.quit_time)

        # TODO: include command line arguments when some are added
        if 'main' in cfg:
            client.setup_broker(cfg['main'])
            client.setup_reporter(cfg['main'])
        else:  # use defaults
            client.setup_broker({})
            client.setup_reporter({})

        # These components are all handled almost identically.

        # EventSinks
        configs = __join_configs_with_args(cfg.get('eventsinks', []), args.event_sinks \
            if args is not None and args.event_sinks is not None else [])
        client.setup_components(configs, 'scale_client.event_sinks', 'event sinks', __make_event_sink, client.__reporter)

        # Set defaults if none were made
        if len(client.__reporter.get_sinks()) == 0:
            log.info("No event_sinks loaded: adding default LogEventSink")
            from ..event_sinks.log_event_sink import LogEventSink
            default_sink = LogEventSink(client.__broker)
            client.__reporter.add_sink(default_sink)

        # Sensors
        configs = __join_configs_with_args(cfg.get('sensors', []), args.sensors \
            if args is not None and args.sensors is not None else [])
        client.setup_components(configs, 'scale_client.sensors', 'sensors', __make_sensor)
        # Networks
        configs = cfg.get('networks', [])
        # TODO: how to add arguments for this?
        client.setup_components(configs, 'scale_client.network', 'network')
        # Applications
        configs = __join_configs_with_args(cfg.get('applications', []), args.applications \
            if args is not None and args.applications is not None else [])
        client.setup_components(configs, 'scale_client.applications', 'applications')

        # TODO: set some defaults if no applications, sensors, or networking components are enabled (heartbeat?)

        return client

    @classmethod
    def _build_config_file_path(cls, filename):
        """Returns the complete path to the given config filename,
        assuming it's been placed in the proper 'config' directory
        or the filename is an absolute path."""
        if os.path.exists(filename):
            return filename
        res = os.path.join(os.path.dirname(__file__), '..', 'config', filename)
        if not os.path.exists(res):
            raise ValueError("requested config file %s does not exist!" % filename)
        return res

    @classmethod
    def parse_args(cls, args=None):
        """
        Parses the given arguments (formatted like sys.argv) or returns default configuration if None specified.
        :param args:
        :return:
        """
        # ArgumentParser.add_argument(name or flags...[, action][, nargs][, const][, default][, type][, choices][, required][, help][, metavar][, dest])
        # action is one of: store[_const,_true,_false], append[_const], count
        # nargs is one of: N, ?(defaults to const when no args), *, +, argparse.REMAINDER
        # help supports %(var)s: help='default value is %(default)s'

        test_default_quit_time = 20
        test_config_filename = 'test_config.yml'
        default_config_filename = cls._build_config_file_path('default_config.yml')

        parser = argparse.ArgumentParser(description='''Scale Client main process.  You can specify a configuration
        file for generating the client's components that will run and/or manually configure them using command
        line arguments (NOTE: these may overwrite parameters in the configuration file if there are conflicts,
        but things like sensors, apps, etc. will be interpreted as additional components).''')

        # Configure what components run
        config_group = parser.add_mutually_exclusive_group()
        config_group.add_argument('--config-file', '-f', type=str, dest='config_filename',
                            default=None,
                            help='''file from which to read configuration (NOTE: if you don't
                            specify an absolute path, SCALE assumes you're referring to a relative
                            path within the 'config' directory).  Default is %s when no
                            manual configurations specified.  If manual configurations are in use,
                            no configuration file is used unless you explicitly set one.''' % default_config_filename)
        config_group.add_argument('--test', '-t', action='store_true',
                            help='''run client with simple test configuration found in file %s
                            (publishes dummy sensor data to simple logging sink).
                            It also quits after %d seconds if you don't specify --quit-time'''
                                 % (test_config_filename, test_default_quit_time))

        # Manually configure components
        parser.add_argument('--sensors', '-s', type=str, nargs='+', default=None,
                            help='''manually specify sensors (and their configurations) to run.
                            Arguments should be in YAML format e.g. can specify two sensors using
                            JSON: --sensors '{class: "heartbeat_virtual_sensor.HeartbeatVirtualSensor",
                            dev_name: "hb0", interval: 5}' '{class:
                             "dummy_sensors.dummy_gas_virtual_sensor.DummyGasVirtualSensor",
                             dev_name: "gas0", interval: 3}'
                            ''')
        parser.add_argument('--applications', '-a', type=str, nargs='+', default=None,
                            help='''manually specify applications (and their configurations) to run.
                            See --sensors help description for example.''')
        parser.add_argument('--event-sinks', '-e', type=str, nargs='+', default=None, dest='event_sinks',
                            help='''manually specify event sinks (and their configurations) to run.
                            See --sensors help description for example.''')
        parser.add_argument('--network', '-n', type=str, nargs='+', default=None,
                            help='''manually specify network components (and their configurations) to run.
                            See --sensors help description for example.''')

        # Misc config params
        parser.add_argument('--log-level', type=str, default='WARNING', dest='log_level',
                            help='''one of debug, info, error, warning''')
        parser.add_argument('--quit-time', '-q', type=int, default=None, dest='quit_time',
                            help='''quit the client after specified number of seconds
                             (default is to never quit)''')

        parsed_args = parser.parse_args(args)


        # Correct configuration filename
        if parsed_args.test:
            parsed_args.config_filename = cls._build_config_file_path(test_config_filename)
        elif parsed_args.config_filename is not None:
            parsed_args.config_filename = cls._build_config_file_path(parsed_args.config_filename)
        # Set default config file if no files or manual configurations are specified
        elif parsed_args.config_filename is None and not any((parsed_args.sensors, parsed_args.applications,
                                                             parsed_args.event_sinks, parsed_args.network)):
            parsed_args.config_filename = default_config_filename

        # Sanity check that we support requested options fully
        if parsed_args.network is not None:
            raise NotImplementedError("--network option not yet fully supported!")

        # Testing configuration quits after a time
        if parsed_args.test and parsed_args.quit_time is None:
            parsed_args.quit_time = test_default_quit_time

        return parsed_args


def _get_class_by_name(kls):
    """Imports and returns a class reference for the full module name specified in regular Python import format"""

    # The following code taken from http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def main():
    args = ScaleClient.parse_args(sys.argv[1:])

    # Seem to have to do this here rather than using logging.setLevel as the latter appears to not work,
    # likely due to the fact that calling it here only affects this module.  Really we want to call this from the root
    # logger (scale_client.?) to affect the whole hierarchy right?
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    global log
    log = logging.getLogger(__name__)

    client = ScaleClient.build_from_configuration_parameters(args.config_filename, args)
    client.run()


if __name__ == '__main__':
    main()
