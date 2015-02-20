from scale_client.sensors.virtual_sensor import VirtualSensor
#import RPi.GPIO as GPIO

class GPIOVirtualSensor(VirtualSensor):
	def __init__(self, broker, device, gpio_pin):
		VirtualSensor.__init__(self, broker, device)
		self._pin = gpio_pin
		self._GPIO = None

	def connect(self):
		# use P1 GPIO pin numbering convention
		if self._GPIO is None:
			import RPi.GPIO as GPIO

			self._GPIO = GPIO

		self._GPIO.setmode(GPIO.BCM)
		# set up GPIO channel
		self._GPIO.setup(self._pin, GPIO.IN)
		return True
