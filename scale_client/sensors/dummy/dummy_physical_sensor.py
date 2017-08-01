from scale_client.sensors.physical_sensor import PhysicalSensor


import logging
log = logging.getLogger(__name__)


class DummyPhysicalSensor(PhysicalSensor):
    """
    A DummyPhysicalSensor is a special type of PhysicalSensor that aims to act just like a derived
    PhysicalSensor class but does not actually manage a physical sensor device.  It generates dummy
    data (useful for testing) and has a dummy DeviceDescriptor.  Currently, this doesn't do anything
    else, but you should subclass your dummy sensors from this one in order to ensure that future
    enhancements that manage a PhysicalSensor know that this class isn't actually managing a real
    physical sensing device.
    """

    def __init__(self, broker, device=None, **kwargs):
        if device is None:
            device = "dummy_device"
        super(DummyPhysicalSensor, self).__init__(broker, device=device, **kwargs)
