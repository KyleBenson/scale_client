from scale_client.core import application
import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class VirtualSensor(application):
    """
    VirtualSensors represent an abstract sensor feed, which may be raw data coming directly from a device, data
    coming from a remote device, or even events detected by other VirtualSensors.

    Open implementation questions:
      1) How to handle sampling rates, modifying priorities, and turning sensors on/off remotely?
      2)
    """

    def __init__(self, broker, device):
        super(VirtualSensor, self).__init__(self, broker)
        self.device = device

    def get_type(self):
        raise NotImplementedError()

    def connect(self):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def policy_check(self, data):
        raise NotImplementedError()

    def report_event(self, ls_event):
        for event in ls_event:
            log.debug("Event added to queue by VS: %s" % event)
            self._broker.put(event)

    def run(self):
        while True:
            data = self.read()
            self.report_event(self.policy_check(data))
