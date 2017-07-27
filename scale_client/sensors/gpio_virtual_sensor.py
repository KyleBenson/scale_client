from scale_client.sensors.virtual_sensor import VirtualSensor


class GPIOVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, interval=1, gpio_pin=None, **kwargs):
        super(GPIOVirtualSensor, self).__init__(broker, device, interval, **kwargs)
        self._pin = gpio_pin
        self._GPIO = None

    def on_start(self):
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
