from scale_client.core.device_descriptor import DeviceDescriptor
from scale_client.sensors.virtual_sensor import VirtualSensor

import logging

from scale_client.util import uri

log = logging.getLogger(__name__)


class PhysicalSensor(VirtualSensor):
    """
    A PhysicalSensor directly manages a physical sensing device attached to (or on board) the
     scale client's host. This is mostly a convention for establishing this contract, but in
     the future it may serve as a point of optimizing physical resource management.
    """

    def __init__(self, broker, device=None, **kwargs):
        """
        :param broker:
        :param device: a DeviceDescriptor for the physical sensing device that will be included in SensedEvents this sensor publishes (default creates one referencing the PhysicalSensor and its path)
        :type device: scale_client.core.device_descriptor.DeviceDescriptor
        :return:
        """
        super(PhysicalSensor, self).__init__(broker, **kwargs)

        # Try to create a DeviceDescriptor from the device specified if we don't have one.
        if device is None:
            device = DeviceDescriptor(self, path=self.path)
            log.debug("Setting default device description for sensor %s to %s" % (self, device))
        elif not isinstance(device, DeviceDescriptor):
            try:
                device = DeviceDescriptor.from_path(device)
            except (ValueError, TypeError):
                device = DeviceDescriptor(device)
        self.device = device

    # TODO: decide if we should do this; unclear that we want to since the path should point to the App,
    # not the device itself.  Maybe that should still be a field in the event schema?
    # @property
    # def path(self):
    #     """
    #     The canonical path for a PhysicalSensor is typically derived from that of its device.
    #     :return:
    #     """
    #     return uri.build_uri(relative_path="sensors/%s" % self.name)
