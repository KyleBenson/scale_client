from scale_client.util import uri


class DeviceDescriptor(object):
    """
    A DeviceDescriptor identifies a physical device within the scale client's node.
    For example, this can represent a physical sensor from which a reading was taken
    or it can represent a piece of hardware such as storage or a network card.
    The purpose is really just to separate these types of optional fields from the
    VirtualSensor (really PhysicalSensor) and SensedEvent classes.
    It isn't really used for much other than storing these fields...
    """

    def __init__(self, device, path=None, name=None, description=None,
                 platform=None, model=None, chipset=None, manufacturer=None, **kwargs):
        """
        You must specify at least one of device, path, or name to make a meaningful instance.
        The latter two can be derived from the first e.g. self.name --> self.device when name is unspecified

        :param device: pointer to the device, VirtualSensor, or a simple string
                       that will be treated just like name
        :param path: URI at which the device can be found e.g. file:/dev/usb0 or
        local:/scale/sensors/heartbeat or coap://1.1.1.1/scale/sensors/temperature
        :param name: short human-readable name
        :param description: longer human-readable description of what the device does, how to interpret data or interact, etc.
        :param platform:
        :param model:
        :param chipset:
        :param manufacturer:
        :param kwargs: any remaining arguments will be stored in a metadata field
        """

        # These are the important attributes: path and name can be unspecified and derived from the device's
        # attribute of the same name
        self.device = device
        self._path = path
        self._name = name

        # The rest of these are purely optional
        self.metadata = kwargs.copy()
        self.description = description
        self.platform = platform
        self.model = model
        self.chipset = chipset
        self.manufacturer = manufacturer

        if not self.device and not self._path and not self._name:
            raise ValueError("at least one of device, path, or name must be unique meaningful values to make a proper DeviceDescriptor!")

    @property
    def name(self):
        if self._name is None:
            try:
                return self.device.name
            except AttributeError:
                return str(self.device)

    @property
    def path(self):
        """
        If the path was unspecified at creation time, we dynamically try to get it from the device or
        build a default version in order to ensure its path is always available.
        :return:
        """
        if self._path is None:
            try:
                return self.device.path
            except AttributeError:
                self._path = uri.build_uri(relative_path='devices/%s' % self.name)
        return self._path

    @classmethod
    def from_path(cls, path):
        """
        Creates a new DeviceDescriptor from the given path in URI-like format.
        This simple implementation will just assume that the device's name is the last part of the path i.e. after last '/'
        :param path:
        :return:
        """
        # XXX: should probably use some external library for handling paths better...
        assert isinstance(path, basestring), "non-string paths not supported! got %s" % path
        dev = path
        while dev.endswith('/'):
            dev = dev[:-1]
        dev = dev[dev.rfind('/') + 1:]

        return DeviceDescriptor(dev, path=path, name=dev)

    def __eq__(self, other):
        """
        Basic equality check (using name and path) mainly used for testing.
        :param other:
        :return:
        """
        return self.name == other.name and ((self.path == other.path) if (self.path is not None and other.path is not None) else True)

    def __repr__(self):
        return "DeviceDescriptor (dev=%s, path=%s)" % (self.device, self.path)