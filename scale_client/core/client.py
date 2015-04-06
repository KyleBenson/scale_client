#!/usr/bin/python

import time, yaml, logging, argparse, os.path
log = None

from Queue import Queue

from scale_client.core.device_descriptor import DeviceDescriptor
#import scale_client.event_sinks as event_sinks, scale_client.sensors as sensors

from event_reporter import EventReporter
# TODO: obfuscate this within a Broker class
from circuits.core.manager import Manager as Broker


class ScaleClient:
    """This class parses a configuration file and subsequently creates, configures, and manages each component of the
    overall Scale Client software.
    """
    def __init__(self, config_filename):
        self.__broker = None
        self.__reporter = None
        self.__sensors = []
        self.__applications = None
        try:
            log.info("Reading config file: %s" % config_filename)
            with open(config_filename) as cfile:
                cfg = yaml.load(cfile)
                # lower-case all top-level headings to tolerate different capitalizations
                cfg = {k.lower(): v for k, v in cfg.items()}

                # verify required entries present
                # required_entries = ('main',)
                # for ent in required_entries:
                #     if ent not in cfg:
                #         raise Exception("Required entry %s not present in config file." % ent)

                # call appropriate handlers for each section in the appropriate order

                if 'main' in cfg:
                    self.setup_broker(cfg['main'])
                    self.setup_reporter(cfg['main'])
                else:
                    self.setup_broker({})
                    self.setup_reporter({})
                if 'eventsinks' in cfg:
                    self.setup_event_sinks(cfg['eventsinks'])
                if 'sensors' in cfg:
                    self.setup_sensors(cfg['sensors'])
                if 'network' in cfg:
                    self.setup_sensors(cfg['network'])
                if 'applications' in cfg:
                    self.setup_applications(cfg['applications'])

        except IOError as e:
            log.error("Error reading config file: %s" % e)
            exit(1)

    def setup_reporter(self, cfg):

        if self.__broker is None:
            self.setup_broker(cfg)

        self.__reporter = EventReporter(self.__broker)

    def setup_broker(self, cfg):
        """
        Currently only creates a dummy Broker object for registering Applications to.

        :param cfg:
        :return:
        """
        self.__broker = Broker()

    def setup_event_sinks(self, sink_configurations):
        for sink_config in (sink.values()[0] for sink in sink_configurations):
            # need to get class definition to call constructor
            if 'class' not in sink_config:
                log.warn("Skipping EventSink with no class definition: %s" % sink_config)
                continue
            try:
                # this line lets us tolerate just e.g. mqtt_event_sink.MQTTEventSink as a relative pathname
                cls_name = sink_config['class'] if 'scale_client.event_sinks' in sink_config['class']\
                    else 'scale_client.event_sinks.' + sink_config['class']
                cls = self._get_class_by_name(cls_name)

                # make a copy of config so we can tweak it to expose only correct kwargs
                new_sink_config = sink_config.copy()
                new_sink_config.pop('class')

                sink = cls(self.__broker, **new_sink_config)

                self.__reporter.add_sink(sink)
                log.info("EventSink created from config: %s" % sink_config)
            except Exception as e:
                log.error("Unexpected error while creating EventSink: %s" % e)

    def setup_sensors(self, sensor_configurations):
        n_sensors = 0
        for sensor_config in (c.values()[0] for c in sensor_configurations):
            # need to get class definition to call constructor
            if 'class' not in sensor_config:
                log.warn("Skipping virtual sensor with no class definition: %s" % sensor_config)
                continue

            try:
                cls_name = sensor_config['class'] if 'scale_client.sensors' in sensor_config['class']\
                    else 'scale_client.sensors.' + sensor_config['class']
                cls = self._get_class_by_name(cls_name)

                # copy config s so we can tweak it as necessary to expose only correct kwargs
                new_sensor_config = sensor_config.copy()
                new_sensor_config.pop('class')
                new_sensor_config.pop('dev_name')

                cls(self.__broker, device=DeviceDescriptor(new_sensor_config.get("dev_name", "vs%i" % n_sensors)),
                    **new_sensor_config)
                n_sensors += 1
                log.info("Virtual sensor created from config: %s" % sensor_config)

            except Exception as e:
                log.error("Unexpected error (%s) while creating virtual sensor: %s" % (e, sensor_config))
                continue

    def run(self):
        """Currently just loop forever to allow the other threads to do their work."""
        # TODO: handle this with less overhead?
	log.debug('hi there')
	print 'hi there'
        self.__broker.run()

    def _get_class_by_name(self,kls):
        """Imports and returns a class reference for the full module name specified in regular Python import format"""
        # TODO: download definition from some repository if necessary

        # The following code taken from http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m


def parse_args():
    """
# ArgumentParser.add_argument(name or flags...[, action][, nargs][, const][, default][, type][, choices][, required][, help][, metavar][, dest])
# action is one of: store[_const,_true,_false], append[_const], count
# nargs is one of: N, ?(defaults to const when no args), *, +, argparse.REMAINDER
# help supports %(var)s: help='default value is %(default)s'
    """

    parser = argparse.ArgumentParser(description="Scale Client main process")

    parser.add_argument('--config', type=str,
                        # config files are located in a different directory
                        default=os.path.join(os.path.dirname(__file__), '..', 'config', 'default_config.yml'),
                        help='''file from which to read configuration''')
    parser.add_argument('--log-level', type=str, default='WARNING', dest='log_level',
                        help='''one of debug, info, error, warning''')

    return parser.parse_args()


def main():
    args = parse_args()

    # Seem to have to do this here rather than using logging.setLevel as the latter appears to not work,
    # likely due to the fact that calling it here only affects this module.  Really we want to call this from the root
    # logger (scale_client.?) to affect the whole hierarchy right?
    # TODO: call this in scale_client.__main__.py?
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    global log
    log = logging.getLogger(__name__)

    client = ScaleClient(args.config)
    client.run()

# this can be used to wait for a network connection to become available.  something like this will need to live in the network manager...
"""
hasNetwork = False
while(hasNetwork != True):
	try:
		response = urllib2.urlopen('http://www.google.com', timeout = 2)
		hasNetwork = True
	except urllib2.URLError:
		time.sleep(5)
		continue
"""

if __name__ == '__main__':
    main()
