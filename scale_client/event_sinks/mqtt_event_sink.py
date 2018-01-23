import logging

from scale_client.util import uri

log = logging.getLogger(__name__)
import socket

from event_sink import EventSink
from uuid import getnode as get_mac

from scale_client.networks.mqtt_application import MqttApplication, MQTT_ERR_CODE_NO_CONN, MQTT_RET_CODE_SUCCESS


class MQTTEventSink(MqttApplication, EventSink):
    def __init__(self, broker,
                topic="iot-1/d/%012x/evt/%s/json",
                **kwargs):
        super(MQTTEventSink, self).__init__(broker=broker, **kwargs)

        self._topic_format = topic
        self._topic = self._topic_format % (0, "%s")

    def _on_connect(self, mqtt_client, obj, rc):
        self._topic = self._topic_format % (get_mac(), "%s")
        super(MQTTEventSink, self)._on_connect(mqtt_client, obj, rc)

    def _on_publish(self, mqtt_client, obj, mid):
        #log.debug("MQTT publisher published: " + str(mid))
        pass

    def send_event(self, event):
        encoded_event = self.encode_event(event)
        # Fill in the blank "%s" left in self._topic
        topic_event_type = event.event_type
        topic = self._topic % topic_event_type

        # HACK: for mesh networking feature,
        # Check to see if event is from neighbors 
        # and need to be published to Mqtt server
        # TODO: move this logic to event_reporter.  Maybe we run a different mesh_event_reporter?
        # Can use the is_local check done in event_reporter, but should verify it'll work during mesh refactor...
        try:
            if "published" in event.metadata:
                if event.metadata["published"] == 1:
                    return True
                else:
                    del event.metadata["published"]
        except KeyError as e:
            log.error("event encoding not as expected for original scale client mesh networking!\n%s" % e.message)

        # Publish message
        res, mid = self.mqtt_publish(encoded_event, topic)
        if res == MQTT_RET_CODE_SUCCESS:
            log.info("MQTT message published to " + topic)
        elif res == MQTT_ERR_CODE_NO_CONN:
            log.error("MQTT publisher failure: No connection")
            return False
        else:
            log.error("MQTT publisher failure: Unknown error")
            return False
        return True

    def check_available(self, event):
        # If we aren't currently running, try connecting.
        if not self.is_connected:
            if not self._try_connect():
                log.error("MQTT publisher failure: Cannot connect")
                return False
        return self.is_connected and super(MQTTEventSink, self).check_available(event)

    def encode_event(self, event):
        """Sets the source to include our host IP address so that a subscriber can find it.  Doesn't permanently change
        the event as it resets the source afterwards."""
        old_source = event.source
        hostname = socket.gethostbyname(socket.gethostname())
        event.source = uri.get_remote_uri(self.path, protocol='mqtt', host=hostname, port=self._client._port)
        res = super(MQTTEventSink, self).encode_event(event)
        event.source = old_source
        return res
