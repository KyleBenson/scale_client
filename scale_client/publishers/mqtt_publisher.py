import socket

import mosquitto
from mosquitto import Mosquitto

import logging
log = logging.getLogger(__name__)

from scale_client.publishers.publisher import Publisher
from uuid import getnode as get_mac


class MQTTPublisher(Publisher):
    def __init__(self, name='MQTT', queue_size=100, callback=None,
                 topic="iot-1/d/%012x/evt/%s/json" % (get_mac(), "%s"),
                hostname=None,
                hostport=1883,
                username=None,
                password=None,
                keepalive=60):
        Publisher.__init__(self, name, queue_size, callback)
        self._client = Mosquitto()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._topic = topic

        self._hostname = hostname
        self._hostport = hostport
        self._username = username
        self._password = password
        self._keepalive = keepalive

        self._loopflag = False

    def _on_connect(self, mosq, obj, rc):
        log.debug("MQTT publisher connected: " + str(rc))

    def _on_disconnect(self, mosq, obj, rc):
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
        self._loopflag = True
        return True

    def connect(self):
        return self._try_connect()

    def send(self, event):
        self._queue.put(event)

    def publish(self, encoded_event):
        # Fill in the blank "%s" left in self._topic
        import json

        event = json.loads(encoded_event)
        topic_event_type = event["d"]["event"]
        topic = self._topic % topic_event_type

        # Publish message
        res, mid = self._client.publish(topic, encoded_event)
        if res == mosquitto.MOSQ_ERR_SUCCESS:
            log.info("MQTT message published to " + topic)
        elif res == mosquitto.MOSQ_ERR_NO_CONN:
            log.error("MQTT publisher failure: No connection")
            return False
        else:
            log.error("MQTT publisher failure: Unknown error")
            return False
        return True

    def encode_event(self, event):
        encoded_event = event.to_json()
        return encoded_event

    def check_available(self, event):
        if not self._loopflag:
            if not self._try_connect():
                log.error("MQTT publisher failure: Cannot connect")
                return False

        if self._queue.full():
            return False
        return True
