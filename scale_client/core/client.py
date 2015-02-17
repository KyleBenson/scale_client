#!/usr/bin/python

import time, yaml, sys, logging, argparse, os.path
log = None

from Queue import Queue

from scale_client.core.device_descriptor import DeviceDescriptor
import scale_client.publishers as publishers, scale_client.sensors as sensors

from event_reporter import EventReporter


class ScaleClient:
    """This class parses a configuration file and subsequently creates, configures, and manages each component of the
    overall Scale Client software.
    """
    def __init__(self, config_filename):
        try:
            with open(config_filename) as cfile:
                cfg = yaml.load(cfile)
                # lower-case all top-level headings to tolerate different capitalizations
                cfg = {k.lower(): v for k, v in cfg.items()}

                # verify required entries present
                required_entries = ('main',)
                for ent in required_entries:
                    if ent not in cfg:
                        raise Exception("Required entry %s not present in config file." % ent)

                # call appropriate handlers for each section in the appropriate order

                if 'main' in cfg:
                    self.setup_reporter(cfg['main'])
                else:
                    self.setup_reporter({})
                if 'publishers' in cfg:
                    self.setup_publishers(cfg['publishers'])
                if 'sensors' in cfg:
                    self.setup_sensors(cfg['sensors'])

        except IOError as e:
            log.error("Error reading config file: %s" % e)

    def setup_reporter(self, cfg):

        # Create sensed event queue
        qsize = cfg['event_queue_size'] if 'event_queue_size' in cfg else 4096
        self.queue = Queue(qsize)

        # Create and start event reporter
        self.reporter = EventReporter(self.queue)
        self.reporter.daemon = True
        self.reporter.start()

    def setup_publishers(self, publishers):
        for p in (pub.values()[0] for pub in publishers):
            # need to get class definition to call constructor
            if 'class' not in p:
                log.warn("Skipping publisher with no class definition: %s" % p)
                continue

            # this line lets us tolerate just e.g. mqtt_publisher.MQTTPublisher as a relative pathname
            cls_name = p['class'] if 'scale_client.publishers' in p['class'] else 'scale_client.publishers.' + p['class']
            cls = self._get_class_by_name(cls_name)

            # make a copy of config so we can tweak it to expose only correct kwargs
            newp = p.copy()
            # TODO: not have to do this here??
            newp['callback'] = self.reporter.send_false_callback
            newp.pop('class')

            try:
                pub = cls(**newp)
                if pub.connect():
                    self.reporter.append_publisher(pub)
                    pub.daemon = True
                    pub.start()
                else:
                    log.warn("Error connecting publisher after configuration: %s" % p)
                    pass

                log.info("Publisher created from config: %s" % p)
            except Exception as e:
                log.error("Unexpected error while creating publisher: %s" % e)

    def setup_sensors(self, cfg):
        # Create and start each virtual sensor listed in config
        ls_vs = []
        for s in (c.values()[0] for c in cfg):
            # need to get class definition to call constructor
            if 'class' not in s:
                log.warn("Skipping virtual sensor with no class definition: %s" % s)
                continue

            try:
                cls_name = s['class'] if 'scale_client.sensors' in s['class'] else 'scale_client.sensors.' + s['class']
                cls = self._get_class_by_name(cls_name)

                # copy config s so we can tweak it as necessary to expose only correct kwargs
                news = s.copy()
                news.pop('class')
                news.pop('dev_name')

                vs = cls(self.queue, DeviceDescriptor(news.get("dev_name", "vs%i" % len(ls_vs))), **news)
                if vs.connect():
                    ls_vs.append(vs)
                else:
                    log.warn("Error connecting virtual sensor after configuration: %s" % s)
                    pass

                log.info("Virtual sensor created from config: %s" % s)

            except Exception as e:
                log.error("Unexpected error (%s) while creating virtual sensor: %s" % (e, s))
                continue

        # Start all the sensors
        for vs_j in ls_vs:
            vs_j.daemon = True
            vs_j.start()

    def run(self):
        """Currently just loop forever to allow the other threads to do their work."""
        # TODO: handle this with less overhead?
        while True:
            time.sleep(1)

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

    parser.add_argument('--config', type=str, nargs=1,
                        default=os.path.join(os.path.dirname(__file__), 'default_config.yml'),
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
