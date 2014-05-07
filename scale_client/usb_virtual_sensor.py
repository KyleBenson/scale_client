from virtual_sensor import VirtualSensor

class USBVirtualSensor(VirtualSensor):
	def __init__(self, queue, device):
		VirtualSensor.__init__(self, queue, device)

