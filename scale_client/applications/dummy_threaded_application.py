from time import sleep
from scale_client.core.threaded_application import ThreadedApplication

import logging
log = logging.getLogger(__name__)


def f(nsecs):
    while True:
        log.debug("separate ThreadedApplication is just sleeping...")
        sleep(nsecs)


class DummyThreadedApplication(ThreadedApplication):
    """
    This class shows a simple example of how to use the THreadedApplication
    class to accomplish running some task in the background using another
    thread/process.
    """

    def on_start(self):
        self.run_in_background(f, 2)
