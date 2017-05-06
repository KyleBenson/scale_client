import socket
import json

import paho.mqtt.client
from paho.mqtt.client import Client as Paho

import logging
log = logging.getLogger(__name__)

from event_sink import EventSink
from uuid import getnode as get_mac


class MQTTEventSink(EventSink):
    def __init__(self, broker,
                topic="iot-1/d/%012x/evt/%s/json",
                hostname=None,
                hostport=1883,
                username=None,
                password=None,
                keepalive=60):
        EventSink.__init__(self, broker)
        self._client = Paho()
        self._client.on_connect = \
                lambda mosq, obj, rc: self._on_connect(mosq, obj, rc)
        self._client.on_disconnect = \
                lambda mosq, obj, rc: self._on_disconnect(mosq, obj, rc)
        self._client.on_publish = \
                lambda mosq, obj, mid: self._on_publish(mosq, obj, mid)
        self._topic_format = topic
        self._topic = self._topic_format % (0, "%s")

        self._hostname = hostname
        self._hostport = hostport
        self._username = username
        self._password = password
        self._keepalive = keepalive

        self._is_connected = False

    def _on_connect(self, mosq, obj, rc):
        self._topic = self._topic_format % (get_mac(), "%s")
        log.debug("MQTT publisher connected: " + str(rc))
        self._is_connected = True

    def _on_disconnect(self, mosq, obj, rc):
        # sink will try reconnecting once EventReporter queries if it's available.
        self._is_connected = False
        log.debug("MQTT publisher disconnected: " + str(rc))

    def _on_publish(self, mosq, obj, mid):
        #log.debug("MQTT publisher published: " + str(mid))
        pass

    def _try_connect(self):
        if self._username is not None and self._password is not None:
            self._client.username_pw_set(self._username, self._password)
        try:
            self._client.connect(self._hostname, self._hostport, self._keepalive)
        except socket.gaierror:
            return False
        self._client.loop_start()
        return True

    def on_start(self):
        return self._try_connect()

    def send_event(self, event):
        encoded_event = self.encode_event(event)
        # Fill in the blank "%s" left in self._topic
        topic_event_type = event.get_type()
        topic = self._topic % topic_event_type

        # HACK: for mesh networking feature,
        # Check to see if event is from neighbors 
        # and need to be published to Mqtt server
        # TODO: move this logic to event_reporter.  Maybe we run a different mesh_event_reporter?
        try:
            if "published" in event.data:
                if event.data["published"] == 1:
                    return True
                else:
                    del event.data["published"]
        except KeyError as e:
            log.error("event encoding not as expected for original scale client mesh networking!\n%s" % e.message)

        # Publish message
        res, mid = self._client.publish(topic, encoded_event)
        if res == paho.mqtt.client.MQTT_ERR_SUCCESS:
            log.info("MQTT message published to " + topic)
        elif res == paho.mqtt.client.MQTT_ERR_NO_CONN:
            log.error("MQTT publisher failure: No connection")
            return False
        else:
            log.error("MQTT publisher failure: Unknown error")
            return False
        return True

    def check_available(self, event):
        # If we aren't currently running, try connecting.
        if not self._is_connected:
            if not self._try_connect():
                log.error("MQTT publisher failure: Cannot connect")
                return False
        return self._is_connected
