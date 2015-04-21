import socket
import json 

import mosquitto
from mosquitto import Mosquitto

import logging
log = logging.getLogger(__name__)

from uuid import getnode as get_mac
import subprocess


class MqttRelayer():
    def __init__(self,
                topic="iot-1/d/%012x/evt/%s/json" % (get_mac(), "%s"),
                hostname=None,
                hostport=1883,
                username=None,
                password=None,
                keepalive=60):

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
        self._try_connect()

    def _on_connect(self, mosq, obj, rc):
        log.debug("MQTT Relayer publisher connected: " + str(rc))

    def _on_disconnect(self, mosq, obj, rc):
        log.debug("MQTT Relayer publisher disconnected: " + str(rc))

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

    def on_start(self):
        return self._try_connect()

    def send_to_mqtt(self, encoded_event):
        # Fill in the blank "%s" left in self._topic
        import json

        # extract the actual topic string
        event = json.loads(encoded_event)
        topic_event_type = event["d"]["event"]
        topic = self._topic % topic_event_type

        # Publish message
        res, mid = self._client.publish(topic, encoded_event)
        if res == mosquitto.MOSQ_ERR_SUCCESS:
            log.info("MQTT Relayer message published to " + topic)
        elif res == mosquitto.MOSQ_ERR_NO_CONN:
            log.error("MQTT Relayer publisher failure: No connection")
            return False
        else:
            log.error("MQTT Relayer publisher failure: Unknown error")
            return False
        return True

    def check_available(self, event):
        if not self._loopflag:
            if not self._try_connect():
                log.error("MQTT Relayer publisher failure: Cannot connect")
                return False
        # TODO: backpressure?
        return True
