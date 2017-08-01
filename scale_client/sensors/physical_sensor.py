from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
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
        :param device: a DeviceDescriptor for the physical sensing device that will be included in SensedEvents this sensor publishes
        :type device: scale_client.core.device_descriptor.DeviceDescriptor
        :return:
        """
        super(PhysicalSensor, self).__init__(broker, **kwargs)
        if device is None:
            log.warning("Failed to specify a device description for sensor %s" % self)
        self.device = device