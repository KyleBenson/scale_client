#!/usr/bin/python
import json
import sys
import yaml
# These two are just for Errors
import yaml.parser
import yaml.scanner
import logging
import argparse
import os
from functools import reduce

from event_reporter import EventReporter
from application import Application
from broker import Broker
from scale_client.util.common import _get_class_by_name
from scale_client.util.defaults import set_logging_config, DEFAULT_DISABLED_LOG_MODULES, DEFAULT_LOG_FORMAT


class ScaleClient(object):
    """This class parses a configuration file and subsequently creates, configures, and manages each component of the
    overall Scale Client software.
    """
    def __init__(self, quit_time=None, raise_errors=False):
        super(ScaleClient, self).__init__()

        self._quit_time = quit_time
        self._raise_errors = raise_errors

        self.__broker = None
        self.__reporter = None
        self.__sensors = None
        self.__applications = None
        self.__networks = None

    def setup_reporter(self, cfg=None):

        if self.__broker is None:
            self.setup_broker(cfg)

        self.__reporter = EventReporter(self.__broker)

    @property
    def event_reporter(self):
        """
        :rtype: EventReporter
        """
        return self.__reporter

    def setup_broker(self, cfg=None):
        """
        Currently only creates a dummy Broker object for registering Applications to.

        :param cfg:
        :return:
        """
        self.__broker = Broker()
        return self.broker

    @property
    def broker(self):
        """
        :rtype: Broker
        """
        return self.__broker

    def schedule_quit_time(self, quit_time):
        """
        Terminate the client and all Applications at the given time.
        :param quit_time: time to quit after in seconds
        :return:
        """
        # HACK: create a dummy app that just calls Broker.stop() at the requested quit_time.
        # We need to do it in an app like this to get the self variables bound in correctly.
        # This is circuits-specific!
        class QuitApp(Application):
            def _quitter(self):
                log.info("Stopping client...")
                self._broker.stop()

                # TODO: put this in a thread? that comes back and finishes quitting in case it hangs?
                # if you REALLY can't get the client to quit, do this:
                # os._exit(0)

        quit_app = QuitApp(self.__broker)
        quit_app.timed_call(quit_time, QuitApp._quitter)

    def run(self):
        """Currently just loop forever to allow the other threads to do their work."""

        if self._quit_time is not None:
            self.schedule_quit_time(self._quit_time)

        # Run the broker until it, and thus the whole scale client, have a stop event fully propagated
        self.__broker.run()

    def setup_sensors(self, configs):
        """
        Configure the sensors expressed in the name-keyed configs dict.
        :param configs:
        """
        self.__sensors = self.setup_components(configs, 'scale_client.sensors')

    def setup_networks(self, configs):
        """
        Configure the sensors expressed in the name-keyed configs dict.
        :param configs:
        """
        self.__networks = self.setup_components(configs, 'scale_client.networks')

    def setup_applications(self, configs):
        """
        Configure the sensors expressed in the name-keyed configs dict.
        :param configs:
        """
        self.__applications = self.setup_components(configs, 'scale_client.applications')

    def setup_components(self, configs, package_name, helper_fun=None, *args):
        """
        Iterate over each component configuration in configs, import the specified class
        (possibly using package_name as the root for the import statement), and then call
        helper_fun with the class and requested configuration to finish its setup.  If
        helper_fun isn't specified, the default simply calls the class's constructor
        with the given arguments parsed from the configuration.
        :param configs: a dict where each entry is a component to set up; each component has a unique
        name as its key and the value is a dict of parameters, which should at least include
         'class' for importing the class using python's import
        :type configs: dict
        :param package_name: root package_name for the class paths specified
         (these will be classes in the scale_client package e.g. sensors, event_sinks)
        :param helper_fun: responsible for creating the component in question and doing any bookkeeping
        :param args: these positional args will be passed to helper_fun
        :return: list of constructed classes
        """

        if helper_fun is None:
            def helper_fun(_class, broker, **kwargs):
                return _class(broker, *args, **kwargs)

        results = []

        for comp_name, cfg in list(configs.items()):
            # need to get class definition to call constructor
            if 'class' not in cfg:
                log.warn("Skipping %s config with no class definition: %s" % (comp_name, cfg))
                continue

            # try importing the specified class extended by package_name first, then just 'class' if error
            cls_name = '.'.join([package_name, cfg['class']])
            other_cls_name = cfg['class']
            try:
                cls = _get_class_by_name(cls_name)

            except ImportError as e:
                try:
                    cls = _get_class_by_name(other_cls_name)
                except ImportError as e2:
                    log.error("ImportErrors while creating %s class: %s\n"
                              "Did you remember to put the repository in your PYTHONPATH??? "
                              "skipping import..." % (other_cls_name, cfg))
                    log.debug("Errors were: %s (import %s)\n%s (import %s)" % (e, cls_name, e2, other_cls_name))
                    continue
            try: # building the class
                # copy config s so we can tweak it as necessary to expose only correct kwargs
                new_config = cfg.copy()
                new_config.pop('class')
                if 'name' not in new_config:
                    new_config['name'] = comp_name

                res = helper_fun(cls, self.__broker, *args, **new_config)
                results.append(res)
                log.info("%s created from config: %s" % (comp_name, cfg))

            except Exception as e:
                log.error("Unexpected error while creating %s class: %s\nError: %s" % (cls.__name__, cfg, e))
                if self._raise_errors:
                    raise

        return results

    @classmethod
    def build_from_configuration_parameters(cls, config_filename, args=None):
        """
        Builds an instance using the (optionally) specified configuration file.  If any args are specified
        (e.g. from parse_args()), they may overwrite the configurations in the file.  However,
        such args that create sensors, apps, etc. will be interpreted as additional
        parameters for components sharing the same names: IT'S UP TO YOU to ensure there aren't conflicts!
        If config_filename is None, we just build using the specified args.
        :param config_filename: optional filename to read config parameters from
        :param args: optional additional configuration arguments as parsed from command line
        :return:
        """

        # XXX: in case the user doesn't specify a name,
        # this will help auto-generate unique ones in a sequence.
        global __scale_client_n_anon_apps_added__
        __scale_client_n_anon_apps_added__ = 0

        if config_filename is None and args is None:
            raise ValueError("can't build from configuration parameters when both filename and args are None!")

        # Dummy config dict in case no config file
        cfg = {'eventsinks': {}, 'sensors': {}, 'applications': {}, 'networks': {}}

        if config_filename is not None:
            try:
                cfg = cls.load_configuration_file(config_filename)
                # log.debug("Final configuration: %s" % cfg)
            except IOError as e:
                log.error("Error reading config file: %s" % e)
                exit(1)

        def __make_event_sink(_class, broker, event_reporter, **config):
            res = _class(broker, **config)
            event_reporter.add_sink(res)
            return res

        ### BEGIN ACTUAL CONFIG FILE USAGE
        # We call appropriate handlers for each section in the appropriate order,
        # starting by getting any relevant command line parameters to create the client.

        client = cls(quit_time=args.quit_time, raise_errors=args.raise_errors)

        # TODO: include command line arguments when some are added
        if 'main' in cfg:
            client.setup_broker(cfg['main'])
            client.setup_reporter(cfg['main'])
        else:  # use defaults
            client.setup_broker({})
            client.setup_reporter({})

        # These components are all handled almost identically.

        # EventSinks
        configs = cls.__join_configs_with_args(cfg.get('eventsinks', {}), args.event_sinks \
            if args is not None and args.event_sinks is not None else [])
        client.setup_components(configs, 'scale_client.event_sinks', __make_event_sink, client.__reporter)

        # Set defaults if none were made
        if len(client.__reporter.get_sinks()) == 0:
            log.info("No event_sinks loaded: adding default LogEventSink")
            LogEventSink = None
            try:
                from ..event_sinks.log_event_sink import LogEventSink
            except ValueError:
                # relative import error when this script called directly (isn't a package)
                try:
                    from scale_client.event_sinks.log_event_sink import LogEventSink
                except ImportError as e:
                    log.error("can't import LogEventSink! Error: %s" % e)
                    exit(1)
            default_sink = LogEventSink(client.__broker)
            client.__reporter.add_sink(default_sink)

        # Sensors
        log.info("Setting up Sensors...")
        configs = cls.__join_configs_with_args(cfg.get('sensors', {}), args.sensors \
            if args is not None and args.sensors is not None else [], "anon_vs")
        client.setup_sensors(configs)

        # Networks
        log.info("Setting up Networks...")
        configs = cls.__join_configs_with_args(cfg.get('networks', {}), args.networks \
            if args is not None and args.networks is not None else [], "anon_network_app")
        client.setup_networks(configs)

        # Applications
        log.info("Setting up other Applications...")
        configs = cls.__join_configs_with_args(cfg.get('applications', {}), args.applications \
            if args is not None and args.applications is not None else [])
        client.setup_applications(configs)

        # TODO: set some defaults if no applications, sensors, or networking components are enabled (heartbeat?)

        return client

    @staticmethod
    def __join_configs_with_args(configs, relevant_args, anon_component_prefix="anon_app"):
        """
        Join the command-line arguments with the configuration file's parsed args in order to add to
        or even modify the file-specified configuration, if there even was one!
        :param configs:
        :type configs: dict
        :param relevant_args: list of individual YAML-encoded dict-like args, possibly without a top-level key for the name
        :param anon_component_prefix: for anonymous components (no name as config dict key), use this string with
        a unique sequential number appended
        :return:
        """
        new_configs = ScaleClient._parse_yaml_configs(relevant_args, anon_component_prefix)
        return ScaleClient.__merge_configs(new_configs, configs)

    @staticmethod
    def _parse_yaml_configs(args, anon_component_prefix="anon_app"):
        """
        Parses the given list of YAML-encoded config dicts and returns all of them as a dict.
        If one of the args doesn't have a top-level key for the name, a unique one is generated
        for you prefixed with the given parameter
        :param args:
        :param anon_component_prefix: prefix for 'anonymous' component configs with no name
        :return:
        """
        # Configuration files are basically nested dictionaries and the command-line arguments
        # are a list with each element being a dictionary. If the dict in the args has the key
        # 'class', then it is anonymous and we should just give it a sequential unique name to
        # ensure it is run.  If, however, it does not, then we should assume that it's a NAMED
        # configuration and so we can actually use that to overwrite/modify the configurations
        # pulled in from a file.

        new_configs = {}
        for arg in args:
            try:
                arg = yaml.load(arg)
            except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
                raise ValueError("error parsing manual configuration: %s\nError:%s" % (arg, e))

            # If this config is anonymous, give it a unique name and add it to configs
            # since it couldn't possibly overwrite another config entry.
            # NOTE: if user specified a 'name' entry directly, we will still take that later on...
            if 'class' in arg:
                # TODO: perhaps register these names somewhere to ensure uniqueness?
                global __scale_client_n_anon_apps_added__
                unique_key = anon_component_prefix + str(__scale_client_n_anon_apps_added__)
                __scale_client_n_anon_apps_added__ += 1
                new_configs[unique_key] = arg
            else:
                try:
                    new_configs.update(arg)
                except TypeError as e:
                    raise ValueError("error in your manual configuration: %s\n"
                                     "couldn't be interpreted as a dict due to error: %s" % (arg, e))

        return new_configs

    @classmethod
    def __merge_configs(cls, a, b, path=None):
        """Merges values found in b into a if a didn't have them. It does this
        recursively so that dicts as values will be merged too.  If they're lists
        they are merged in a similar way except that the top-level key of each contained
        dict is assumed to be the unique id so that, for example, two entries of
        'TestApp' will take the first one even if the parameters are different."""

        # This function is modeled after:
        # https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge

        if path is None: path = []

        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    cls.__merge_configs(a[key], b[key], path + [str(key)])
                elif isinstance(a[key], list) and isinstance(b[key], list):
                    # Easy enough to merge lists of non-dict items...
                    try:
                        al = set(a[key])
                        bl = set(b[key])
                        bl.update(al)
                        a[key] = list(bl)
                    except (TypeError, AttributeError) as e:
                        log.warning('problem merging lists when merging configurations'
                                    '(are there dict args in one at path %s?):'
                                    '\n%s\n%s\nKeeping the first one due to error %s'
                                    % (path, a[key], b[key], e))
                else:
                    # Same key, but different value type.  This is difficult to
                    # handle so we just keep the value of the first one.
                    pass
            else:
                a[key] = b[key]
        return a

    @classmethod
    def load_configuration_file(cls, config_filename):
        """
        Reads the YAML-based configuration file specified and optionally recurses on itself
        to read other config files that were included in this one.
        :param config_filename:
        :return: the dict-like configuration
        """
        log.info("Reading config file: %s" % config_filename)
        with open(config_filename) as cfile:
            cfg = yaml.load(cfile)
            # lower-case all top-level headings to tolerate different capitalizations
            # also filter out any sections that didn't include anything
            cfg = {k.lower(): v for k, v in cfg.items() if v is not None}

            # Recursively call this function and merge the results back together
            if 'main' in cfg and 'include_config_files' in cfg['main']:
                # We want to do the update in reverse order so that the top-level config file
                # overwrites the lower-level ones (same with left-most sub config).
                sub_cfgs = [cfg]

                for sub_fname in cfg['main']['include_config_files']:
                    log.debug("recursively loading config file %s" % sub_fname)
                    sub_fname = cls._build_config_file_path(sub_fname)
                    sub_cfg = cls.load_configuration_file(sub_fname)
                    sub_cfgs.append(sub_cfg)

                cfg = reduce(cls.__merge_configs, sub_cfgs)

        return cfg

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
                            Arguments should be in YAML format (JSON is a subset of YAML!)
                            e.g. can specify two sensors using:
                            --sensors '{class: "network.heartbeat_virtual_sensor.HeartbeatSensor",
                            interval: 5}' '{class:
                             "dummy.dummy_gas_virtual_sensor.DummyGasPhysicalSensor",
                             name: "gas0", interval: 3}'

                            Alternatively, you can also assign a name to your custom component, which
                            can be used to overwrite or modify one of the same name in your configuration
                            file such as the following to change the actual class definition used:
                            '{TempSensor: {class: "environment.usb_temperature_virtual_sensor.UsbTemperaturePhysicalSensor"}'
                            ''')
        parser.add_argument('--applications', '-a', type=str, nargs='+', default=None,
                            help='''manually specify applications (and their configurations) to run.
                            See --sensors help description for example.''')
        parser.add_argument('--event-sinks', '-e', type=str, nargs='+', default=None, dest='event_sinks',
                            help='''manually specify event sinks (and their configurations) to run.
                            See --sensors help description for example.''')
        parser.add_argument('--networks', '-n', type=str, nargs='+', default=None,
                            help='''manually specify network components (and their configurations) to run.
                            See --sensors help description for example.''')

        # Configure logging
        parser.add_argument('--log-level', type=str, default='WARNING', dest='log_level',
                            help='''one of debug, info, error, warning''')
        parser.add_argument('--enable-log-modules', dest='enable_log_modules', nargs='+', default=(),
                            help='''explicitly enable logging for the specified modules
                            (by default all of %s are disabled)''' % DEFAULT_DISABLED_LOG_MODULES)
        parser.add_argument('--disable-log-modules', dest='disable_log_modules', nargs='+', default=(),
                            help='''explicitly disable logging for the specified modules''')
        parser.add_argument('--format-logging', type=str, default=DEFAULT_LOG_FORMAT, dest='log_format',
                            help='''formats logging as per the given argument (default=%(default)s).
                            NOTE: add timestamp by doing %%(asctime)s''')

        # Misc config params
        parser.add_argument('--quit-time', '-q', type=int, default=None, dest='quit_time',
                            help='''quit the client after specified number of seconds
                             (default is to never quit)''')
        parser.add_argument('--raise-errors', action='store_true', dest='raise_errors',
                            help='''when constructing a component, raise the (non-import) errors to allow printing
                            a stack trace rather than trying to gracefully skip it and logging the error''')

        parsed_args = parser.parse_args(args if args is not None else '')

        # Correct configuration filename
        if parsed_args.test:
            parsed_args.config_filename = cls._build_config_file_path(test_config_filename)
        elif parsed_args.config_filename is not None:
            parsed_args.config_filename = cls._build_config_file_path(parsed_args.config_filename)
        # Set default config file if no files or manual configurations are specified
        elif parsed_args.config_filename is None and not any((parsed_args.sensors, parsed_args.applications,
                                                             parsed_args.event_sinks, parsed_args.networks)):
            parsed_args.config_filename = default_config_filename

        # Testing configuration quits after a time
        if parsed_args.test and parsed_args.quit_time is None:
            parsed_args.quit_time = test_default_quit_time

        return parsed_args


def configure_logging(args):
    """
    Configure logging facility based on requested parameters.
    """

    set_logging_config(level=getattr(logging, args.log_level.upper()), log_format=args.log_format)
    global log
    log = logging.getLogger(__name__)

    # Unless explicitly enabled, disable the following (for log level < WARN):
    disabled_log_modules = set(args.disable_log_modules).union(DEFAULT_DISABLED_LOG_MODULES)
    enabled_log_modules = set(args.enable_log_modules)
    for mod in disabled_log_modules - enabled_log_modules:
        logging.getLogger(mod).setLevel(logging.WARNING)


def make_scale_config(applications=None, sensors=None, sinks=None, networks=None):
    """
    Builds a string to be used on the command line in order to run a scale client with the given configurations.
    NOTE: make sure to properly space your arguments and wrap any newlines in quotes so they aren't interpreted
    as the end of the command by the shell!
    """
    cfg = ""
    if applications is not None:
        cfg += ' --applications %s ' % applications
    if sensors is not None:
        cfg += ' --sensors %s ' % sensors
    if networks is not None:
        cfg += ' --networks %s ' % networks
    if sinks is not None:
        cfg += ' --event-sinks %s ' % sinks
    return cfg


def make_scale_config_entry(class_path, name, cmd_line_format=True, **kwargs):
    """Builds an individual entry for a single SCALE client module that can be fed to the CLI.
    :param cmd_line_format: if True (default), formats the resulting string for use on command line:
        it wraps raw JSON in single quotes as json.dumps wraps strings in double quotes;
        it escapes these double quotes so that 'eval' (su -c) actually sees them in the args it passes to the final command
    NOTE: don't forget to add spaces around each entry if you use multiple!"""
    d = dict(**kwargs)
    # XXX: can't use 'class' as a kwarg in call to dict, so doing it this way...
    d['class'] = class_path
    if cmd_line_format:
        return "'%s' " % json.dumps({name: d}).replace('"', r'\"')
    else:
        return json.dumps({name: d})


def main():
    args = ScaleClient.parse_args(sys.argv[1:])
    configure_logging(args)

    client = ScaleClient.build_from_configuration_parameters(args.config_filename, args)
    client.run()


if __name__ == '__main__':
    main()
