#!/usr/bin/python

import threading
import time
from threading import Thread
from Queue import Queue
from device_descriptor import DeviceDescriptor
from event_reporter import EventReporter
from publisher import Publisher
from mqtt_publisher import MQTTPublisher
from virtual_sensor import VirtualSensor
from heartbeat_virtual_sensor import HeartbeatVirtualSensor as HBVirtualSensor

QUEUE_SIZE = 4096
MQTT_HOSTNAME = "m10.cloudmqtt.com"
MQTT_HOSTPORT = 14664
MQTT_USERNAME = "mqytlrad"
MQTT_PASSWORD = "Q_C2GjJvRQrZ"

# Create message queue
queue = Queue(QUEUE_SIZE)

# Create and start event reporter
reporter = EventReporter(queue)
reporter.daemon = True
reporter.start()

# Create publishers
pb_mqtt = MQTTPublisher(
	topic_prefix = "scale/test"
)
if pb_mqtt.connect(MQTT_HOSTNAME, MQTT_HOSTPORT, MQTT_USERNAME, MQTT_PASSWORD):
	reporter.append_publisher(pb_mqtt)

# Create and start virtual sensors
ls_vs = []
vs_heartbeat = HBVirtualSensor(
	queue,
	DeviceDescriptor("hb0"),
	interval = 5
)
ls_vs.append(vs_heartbeat)
for vs_j in ls_vs:
	vs_j.daemon = True
	vs_j.start()

# Loop forever
while True:
	time.sleep(1)
