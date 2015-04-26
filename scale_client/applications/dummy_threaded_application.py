from time import sleep
from scale_client.core.threaded_application import ThreadedApplication
from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import logging
log = logging.getLogger(__name__)


def f(self, nsecs):
    while True:
        log.debug("separate ThreadedApplication is just sleeping...")
        sleep(nsecs)

class DummyThreadedApplication(ThreadedApplication, Application):
    """
    This class shows a simple example of how to use the ThreadedApplication
    class to accomplish running some task in the background using another
    thread/process.
    """

    def on_start(self):
        self.run_in_background(f, self, 10)
