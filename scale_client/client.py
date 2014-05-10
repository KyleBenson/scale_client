#!/usr/bin/python

import threading
import time
import socket
from threading import Thread
from Queue import Queue
from device_descriptor import DeviceDescriptor
from event_reporter import EventReporter
from publisher import Publisher
from mqtt_publisher import MQTTPublisher
from sigfox_publisher import SigfoxPublisher 
from virtual_sensor import VirtualSensor
from heartbeat_virtual_sensor import HeartbeatVirtualSensor as HBVirtualSensor
from usb_virtual_sensor import USBVirtualSensor
from temperature_virtual_sensor import TemperatureVirtualSensor
from csn_virtual_sensor import CSNVirtualSensor

QUEUE_SIZE = 4096
MQTT_HOSTNAME = "m10.cloudmqtt.com"
MQTT_HOSTPORT = 11094
MQTT_USERNAME = "vbjsfwul"
MQTT_PASSWORD = "xottyHH5j9v2"
CEL_DAEMON_PATH = "temperature-streams"

# Create message queue
queue = Queue(QUEUE_SIZE)

# Create and start event reporter
reporter = EventReporter(queue)
reporter.daemon = True
reporter.start()

# Create MQTT publishers
#file_hostname = open("/etc/hostname", "r")
#str_hostname = file_hostname.readline().rstrip()
#file_hostname.close()
pb_mqtt = MQTTPublisher(
	topic_prefix = "scale/test/" + socket.gethostname()
)
if pb_mqtt.connect(MQTT_HOSTNAME, MQTT_HOSTPORT, MQTT_USERNAME, MQTT_PASSWORD):
	reporter.append_publisher(pb_mqtt)

# Create Sigfox publisher
pb_sigfox = SigfoxPublisher(
	topic_prefix = "scale/test"
)
if (pb_sigfox.connect()):
	reporter.append_publisher(pb_sigfox)

# Create and start virtual sensors
ls_vs = []
vs_heartbeat = HBVirtualSensor(
	queue,
	DeviceDescriptor("hb0"),
	interval = 5
)
if vs_heartbeat.connect():
	ls_vs.append(vs_heartbeat)

vs_temperature = TemperatureVirtualSensor(
	queue,
	DeviceDescriptor("cel0"),
	daemon_path = CEL_DAEMON_PATH,
	threshold = 24.0
)
if vs_temperature.connect():
	ls_vs.append(vs_temperature)

vs_csn = CSNVirtualSensor(
	queue,
	DeviceDescriptor("accel"))
if vs_csn.connect():
	ls_vs.append(vs_csn)

for vs_j in ls_vs:
	vs_j.daemon = True
	vs_j.start()

# Loop forever
while True:
	time.sleep(1)
