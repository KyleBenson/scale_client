import socket
import json

import mosquitto
from mosquitto import Mosquitto

import logging
log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink
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
        self._client = Mosquitto()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._topic_format = topic
        self._topic = self._topic_format % (0, "%s")

        self._hostname = hostname
        self._hostport = hostport
        self._username = username
        self._password = password
        self._keepalive = keepalive

        self._loopflag = False
        self._neta = None

    def _on_connect(self, mosq, obj, rc):
    	self._topic = self._topic_format % (get_mac(), "%s")
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

    def on_start(self):
        return self._try_connect()

    def send(self, encoded_event):
        # Fill in the blank "%s" left in self._topic
        import json

        # extract the actual topic string
        event = json.loads(encoded_event)
        topic_event_type = event["d"]["event"]
        topic = self._topic % topic_event_type

        # Check to see if event is from neighbors 
        # and need to be published to Mqtt server
        if "published" in event["d"]:
            if event["d"]["published"] == 1:
                return True
            else:
                del event["d"]["published"]

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

    def check_available(self, event):
        if self._neta is not None and not self._neta:
            return False
        if not self._loopflag:
            if not self._try_connect():
                log.error("MQTT publisher failure: Cannot connect")
                return False
        return True

    def on_event(self, event, topic):
        et = event.get_type()
        ed = event.get_raw_data()

        if et == "internet_access":
            self._neta = ed

    def encode_event(self, event):
        # return event.to_json()
        return json.dumps({"d": event.to_map()})
