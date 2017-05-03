class DeviceDescriptor:
    """
    Bare-bones device descriptor to identify a device within the client's node.
    For example, this can represent a physical sensor from which a reading
    was taken.  We don't do anything interesting with it currently...
    """
    def __init__(self, device, path = None):
        self.device = device
        self.path = path