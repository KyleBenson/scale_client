from time import sleep
from scale_client.core.threaded_application import ThreadedApplication
from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent
from scale_client.network.scale_network_manager import ScaleNetworkManager

import logging
log = logging.getLogger(__name__)


def f(self, nsecs):
    scale_mesh_network = ScaleNetworkManager(self, 'Scanner')

    while True:
        log.debug("Waking up and scanning neighbors ...")
        scale_mesh_network.scan_all_interfaces()
        scale_mesh_network.scan_neighbors_ip_address()
        scale_mesh_network.display_neighbors()

        log.debug("Done scanning neighbors, going back to sleep and snoozing...")
        sleep(nsecs)

class MeshScanNeighbors(ThreadedApplication, Application):
    """
    This class shows a simple example of how to use the ThreadedApplication
    class to accomplish running some task in the background using another
    thread/process.
    """

    def on_start(self):
        self.run_in_background(f, self, 60)
