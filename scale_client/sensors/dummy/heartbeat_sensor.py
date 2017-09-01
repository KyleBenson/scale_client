import logging
log = logging.getLogger(__name__)

from scale_client.sensors.dummy.dummy_virtual_sensor import DummyVirtualSensor


class HeartbeatSensor(DummyVirtualSensor):
    """
    This sensor simply publishes a heartbeat event every sample_interval seconds, which is
    useful for ensuring a remote client is alive and connected to the data exchange.
    """

    def __init__(self, broker, static_event_data="heartbeat", event_type="hearbeat", sample_interval=5, **kwargs):
        super(HeartbeatSensor, self).__init__(broker=broker, static_event_data=static_event_data,
                                              event_type=event_type, sample_interval=sample_interval, **kwargs)

    DEFAULT_PRIORITY = 10