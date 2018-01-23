import logging
import socket

log = logging.getLogger(__name__)

from scale_client.core.application import Application

from paho.mqtt.client import Client as MqttClient
# these error codes can be imported by other classes to check return status
from paho.mqtt.client import MQTT_ERR_SUCCESS as MQTT_RET_CODE_SUCCESS, MQTT_ERR_NO_CONN as MQTT_ERR_CODE_NO_CONN


class MqttApplication(Application):
    """
    An abstract base Application for running some type of MQTT client-based Application.
    """

    def __init__(self, broker,
                hostname=None,
                hostport=1883,
                username=None,
                password=None,
                keepalive=60,
                **kwargs):
        super(MqttApplication, self).__init__(broker=broker, **kwargs)
        self._client = MqttClient()
        self._client.on_connect = \
                lambda mqtt_client, obj, rc: self._on_connect(mqtt_client, obj, rc)
        self._client.on_disconnect = \
                lambda mqtt_client, obj, rc: self._on_disconnect(mqtt_client, obj, rc)
        self._client.on_publish = \
                lambda mqtt_client, obj, mid: self._on_publish(mqtt_client, obj, mid)
        self._client.on_subscribe = \
                lambda mqtt_client, userdata, mid, qos: self._on_subscribe(mqtt_client, mid, qos)
        self._client.on_message = \
                lambda mqtt_client, userdata, msg: self._on_message(mqtt_client, msg.payload, msg.topic, msg.qos, msg.retain)

        self._hostname = hostname
        self._hostport = hostport
        self._username = username
        self._password = password
        self._keepalive = keepalive

        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    # Your API for pub-sub via MQTT:

    def mqtt_publish(self, raw_data, topic, **kwargs):
        """
        Publishes the given data to the specified topic.
        :param raw_data:
        :type raw_data: str
        :param topic:
        :param kwargs: e.g. qos, retain; passed to self._client.publish
        :return: err_code, msg_id
        """
        return self._client.publish(topic, raw_data, **kwargs)

    def mqtt_subscribe(self, topic, **kwargs):
        """
        Subscribes to the specified topic.
        :param topic:
        :param kwargs: e.g. qos; passed to self._client.publish
        :return: err_code, msg_id
        """
        return self._client.subscribe(topic, **kwargs)

    # To make use of either publish or subscribe, make sure to implement these!

    def _on_publish(self, mqtt_client, obj, mid):
        log.debug("MQTT app %s published msg %d: %s" % (self.name, mid, obj))

    def _on_subscribe(self, mqtt_client, mid, qos):
        log.debug("MQTT app %s subscribe response msg %d: qos=%s" % (self.name, mid, qos))

    def _on_message(self, mqtt_client, payload, topic, qos, retain):
        """Called when a message arrives on a topic we subscribed to."""
        log.debug("MQTT app %s received message on topic %s: %s" % (self.name, topic, payload))

    # You may want to override these functions in your concrete Application, but make sure to call super()!

    def _on_connect(self, mqtt_client, obj, rc):
        log.debug("MQTT app %s connected: %s" % (self.name, str(rc)))
        # need to start AFTER connecting, which is async!
        self._is_connected = True

    def _on_disconnect(self, mqtt_client, obj, rc):
        # sink will try reconnecting once EventReporter queries if it's available.
        self._is_connected = False
        log.debug("MQTT app %s disconnected: %s" % (self.name, str(rc)))

    def _try_connect(self):
        if self._username is not None and self._password is not None:
            self._client.username_pw_set(self._username, self._password)
        try:
            # NOTE: this is an async connection!
            self._client.connect(self._hostname, self._hostport, self._keepalive)
            self._client.loop_start()
        except socket.gaierror:
            return False
        return True

    def on_start(self):
        super(MqttApplication, self).on_start()
        return self._try_connect()
