from scale_client.networks.mqtt_application import MqttApplication
from scale_client.networks.util import process_remote_event
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.sensed_event import SensedEvent
from scale_client.util import uri

import logging
log = logging.getLogger(__name__)


class MqttSensor(MqttApplication, VirtualSensor):
    """
    Subscribes to the MQTT topics specified after connecting to the specified broker.  It parses SensedEvents from any
    messages received (if possible) and publishes the resulting remote events internally.
    """

    def __init__(self, broker, mqtt_subscriptions=tuple(), qos=0, **kwargs):
        """
        :param broker: the INTERNAL SCALE broker; see MqttApplication for the MQTT broker details
        :param mqtt_subscriptions: the MQTT topics to subscribe to
        :param qos: what QoS to subscribe via e.g. 0, 1, 2
        :param kwargs:
        """

        super(MqttSensor, self).__init__(broker, **kwargs)
        self._mqtt_subscriptions = mqtt_subscriptions
        self._qos = qos

    def _on_connect(self, mqtt_client, obj, rc):
        super(MqttSensor, self)._on_connect(mqtt_client, obj, rc)

        # connect to the topics
        for topic in self._mqtt_subscriptions:
            self.mqtt_subscribe(topic, qos=self._qos)

    def _on_message(self, mqtt_client, payload, topic, qos, retain):
        """Publishes the SensedEvent internally upon receiving it"""

        try:
            event = SensedEvent.from_json(payload)
            # NOTE: we probably don't actually have to do this as its source should already be set,
            # but just in case we add additional handling later...
            process_remote_event(event)
        except BaseException as e:
            log.error("failed to parse SensedEvent from JSON payload: %s\nError was: %s" % (payload, e))
            return

        event.metadata['mqtt_topic'] = topic
        event.metadata['mqtt_broker'] = uri.build_uri(scheme='mqtt', path='broker', host=self._hostname, port=self._hostport)
        event.metadata['time_rcvd'] = SensedEvent.get_timestamp()
        self.publish(event)
        log.debug("MqttSensor received SensedEvent from topics %s: %s" % (topic, event))