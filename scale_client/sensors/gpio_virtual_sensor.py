from scale_client.sensors.virtual_sensor import VirtualSensor


class GPIOVirtualSensor(VirtualSensor):
    """
    This class is specifically designed for use with GPIO sensors attached to a Raspberry Pi.
    """
    def __init__(self, broker, device=None, interval=1, gpio_pin=None, **kwargs):
        """
        :param broker:
        :param device:
        :param interval:
        :param gpio_pin: uses P1 GPIO pin numbering convention
        :param kwargs:
        """
        super(GPIOVirtualSensor, self).__init__(broker, device=device, interval=interval, **kwargs)
        self._pin = gpio_pin
        self._GPIO = None

    def on_start(self):
        """
        This actually sets up the GPIO channel for the pin specified in the constructor.
        """
        # use P1 GPIO pin numbering convention
        if self._GPIO is None:
            import RPi.GPIO as GPIO

            self._GPIO = GPIO

        self._GPIO.setmode(GPIO.BCM)
        # set up GPIO channel
        self._GPIO.setup(self._pin, GPIO.IN)

        super(GPIOVirtualSensor, self).on_start()

    def read_raw(self):
        input_value = self._GPIO.input(self._pin)
        return input_value
