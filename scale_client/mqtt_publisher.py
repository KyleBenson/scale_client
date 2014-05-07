import socket
from publisher import Publisher
import mosquitto
from mosquitto import Mosquitto

class MQTTPublisher(Publisher):
	def __init__(self, topic_prefix, topic_suffix = ""):
		self._client = Mosquitto()
		self._client.on_connect = self._on_connect
		self._client.on_disconnect = self._on_disconnect
		self._client.on_publish = self._on_publish
		self._topic_prefix = topic_prefix
		self._topic_suffix = topic_suffix
		self._loopflag = False

	def _on_connect(self, mosq, obj, rc):
		print "MQTT publisher connected: " + str(rc)

	def _on_disconnect(self, mosq, obj, rc):
		print "MQTT publisher disconnected: " + str(rc)

	def _on_publish(self, mosq, obj, mid):
#		print "MQTT publisher published: " + str(mid)
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

	def connect(
		self,
		hostname,
		hostport = 1883,
		username = None,
		password = None,
		keepalive = 60
	):
		self._hostname = hostname
		self._hostport = hostport
		self._username = username
		self._password = password
		self._keepalive = keepalive
		self._try_connect()
		return True

	def send(self, event):
		# Try to connect if not in loop
		if not self._loopflag:
			if not self._try_connect():
				print "MQTT publisher failure: Cannot connect"
				return False

		# Make message from a sensed event
		topic = ""
		if self._topic_prefix != "":
			topic += self._topic_prefix + "/"
		topic += event.sensor
		if self._topic_suffix != "":
			topic += "/" + self._topic+suffix
		msg = event.msg + " @" + str(event.timestamp)

		# Publish message
		res, mid = self._client.publish(topic, msg)
		if res == mosquitto.MOSQ_ERR_SUCCESS:
			print "MQTT message published to " + topic
		elif res == mosquitto.MOSQ_ERR_NO_CONN:
			print "MQTT publisher failure: No connection"
			return False
		else:
			print "MQTT publisher failure: Unknown error"
			return False
		return True
