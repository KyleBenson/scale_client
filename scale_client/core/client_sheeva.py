#!/usr/bin/python

import time
from Queue import Queue
from uuid import getnode as get_mac

from scale_client.core.device_descriptor import DeviceDescriptor
from event_reporter import EventReporter






#from publisher import Publisher
from scale_client.publishers.mqtt_publisher import MQTTPublisher
from scale_client.publishers.sigfox_publisher import SigfoxPublisher
#from virtual_sensor import VirtualSensor
from scale_client.sensors.heartbeat_virtual_sensor import HeartbeatVirtualSensor as HBVirtualSensor
#from usb_virtual_sensor import USBVirtualSensor
from scale_client.sensors.temperature_virtual_sensor import TemperatureVirtualSensor
from scale_client.sensors.csn_virtual_sensor import CSNVirtualSensor

QUEUE_SIZE = 4096
MQTT_HOSTNAME = "dime.smartamerica.io"
MQTT_HOSTPORT = 1883
MQTT_USERNAME = None #"vbjsfwul"
MQTT_PASSWORD = None #"xottyHH5j9v2"
MQTT_TOPIC = "iot-1/d/%012x/evt/%s/json" % (get_mac(), "%s")
CEL_DAEMON_PATH = "temperature-streams"

# Create message queue
queue = Queue(QUEUE_SIZE)

# Create and start event reporter
reporter = EventReporter(queue)
reporter.daemon = True
reporter.start()

ls_pb = []
# Create MQTT publishers

pb_mqtt = MQTTPublisher(
	name = "Sigfox",
	queue_size = 100,
	callback = reporter.send_false_callback,
	topic = MQTT_TOPIC
)
if pb_mqtt.connect(MQTT_HOSTNAME, MQTT_HOSTPORT, MQTT_USERNAME, MQTT_PASSWORD):
	reporter.append_publisher(pb_mqtt)
	ls_pb.append(pb_mqtt)


# Create Sigfox publisher
pb_sigfox = SigfoxPublisher(name = "Sigfox", queue_size = 6, callback =  reporter.send_false_callback)
if (pb_sigfox.connect()):
	reporter.append_publisher(pb_sigfox)
	ls_pb.append(pb_sigfox)

for pb_j in ls_pb:
        pb_j.daemon = True
        pb_j.start()

# Create and start virtual sensors
ls_vs = []
vs_heartbeat = HBVirtualSensor(
	queue,
	DeviceDescriptor("hb0"),
	interval = 60 
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
