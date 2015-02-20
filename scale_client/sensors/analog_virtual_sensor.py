from scale_client.sensors.virtual_sensor import VirtualSensor
#import spidev

class AnalogVirtualSensor(VirtualSensor):
	def __init__(self, broker, device, analog_port):
		VirtualSensor.__init__(self, broker, device)
		if analog_port >3 or analog_port < 0:
			return -1
		self._port = analog_port
		self._spi = None

	def connect(self):
		if self._spi is None:
			import spidev

			self._spi = spidev.SpiDev()
		try:
			self._spi.open(0,0)
		except IOError:
			print "Failed to open analog device: " + self.device.device

			return False
		return True
