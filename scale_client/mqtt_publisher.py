from publisher import Publisher
from mosquitto import Mosquitto

class MQTTPublisher(Publisher):
	def __init__(self, topic_prefix, topic_suffix = ""):
		self._client = Mosquitto()
		self._client.on_connect = self._on_connect
		self._topic_prefix = topic_prefix
		self._topic_suffix = topic_suffix

	def _on_connect(self, mosq, obj, rc):
		print "MQTT publisher connected"

	def connect(
		self,
		hostname,
		hostport = 1883,
		username = None,
		password = None,
		keepalive = 60
	):
		if username is not None and password is not None:
			self._client.username_pw_set(username, password)
		self._client.connect(hostname, hostport, keepalive)
		self._client.loop_start()
		return True

	def send(self, event):
		# Make message from a sensed event
		topic = self._topic_prefix + "/" + event.sensor + "/" + self._topic_suffix
		msg = event.msg + " @" + str(event.timestamp)

		# Publish message
		self._client.publish(topic, msg)
		print "MQTT message published to " + topic
