from time import sleep
from scale_client.core.threaded_application import ThreadedApplication

import logging
log = logging.getLogger(__name__)


def f(self, nsecs):
    while True:
        log.debug("Separate ThreadedApplication is just sleeping...")
        sleep(nsecs)
        log.debug("Separate ThreadedApplication is just snoozing...")
        sleep(nsecs)

class DummyThreadedApplication(ThreadedApplication):
    """
    This class shows a simple example of how to use the ThreadedApplication
    class to accomplish running some task in the background using another
    thread/process.
    """

    def on_start(self):
        super(DummyThreadedApplication, self).on_start()
        self.run_in_background(f, self, 10)
