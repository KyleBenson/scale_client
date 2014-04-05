from virtual_sensor import VirtualSensor
import RPi.GPIO as GPIO

class GPIOVirtualSensor(VirtualSensor):
	def __init__(self, queue, device, gpio_pin):
		VirtualSensor.__init__(self, queue, device)
		self._pin = gpio_pin
		self._GPIO = GPIO

	def connect(self):
                # use P1 GPIO pin numbering convention
                self._GPIO.setmode(GPIO.BCM)
                # set up GPIO channel
                self._GPIO.setup(self._pin, GPIO.IN)
