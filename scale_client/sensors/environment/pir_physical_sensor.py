from scale_client.sensors.gpio_physical_sensor import GpioPhysicalSensor


class PirPhysicalSensor(GpioPhysicalSensor):
    """
    Monitors a passive infrared (PIR) device to detect movement.  Note that
    PIR pretty much only works on warm-blooded living creatures.
    """
    def __init__(self, broker, interval=1, event_type="motion", **kwargs):
        super(PirPhysicalSensor, self).__init__(broker, interval=interval, event_type=event_type, **kwargs)
        self._state = PirPhysicalSensor.IDLE

    DEFAULT_PRIORITY = 7
    IDLE = 0
    ACTIVE = 1

    def policy_check(self, event):
        raw = event.data
        success = False

        # State transitions
        if self._state == PirPhysicalSensor.IDLE and raw == PirPhysicalSensor.ACTIVE:
            self._state = PirPhysicalSensor.ACTIVE
            success = True
        elif self._state == PirPhysicalSensor.ACTIVE and raw == PirPhysicalSensor.IDLE:
            self._state = PirPhysicalSensor.IDLE
            # self._inact_timer = get_time()
            success = True

        return success
