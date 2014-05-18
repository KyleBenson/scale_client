#!/usr/bin/python

import threading
import time
import urllib2
import socket
from threading import Thread
from Queue import Queue
from uuid import getnode as get_mac
from device_descriptor import DeviceDescriptor
from event_reporter import EventReporter
#from publisher import Publisher
from mqtt_publisher import MQTTPublisher
#from virtual_sensor import VirtualSensor
#from gpio_virtual_sensor import GPIOVirtualSensor
#from analog_virtual_sensor import AnalogVirtualSensor
from heartbeat_virtual_sensor import HeartbeatVirtualSensor as HBVirtualSensor
#from pir_virtual_sensor import PIRVirtualSensor 
#from light_virtual_sensor import LightVirtualSensor
#from gas_virtual_sensor import GasVirtualSensor
from dummy_pir_virtual_sensor import DummyPIRVirtualSensor 
from dummy_light_virtual_sensor import DummyLightVirtualSensor
from dummy_gas_virtual_sensor import DummyGasVirtualSensor
from dummy_temperature_virtual_sensor import DummyTemperatureVirtualSensor
from dummy_csn_virtual_sensor import DummyCSNVirtualSensor

QUEUE_SIZE = 4096
MQTT_HOSTNAME = "m2m.eclipse.org"
#MQTT_HOSTNAME = "dime.smartamerica.io"
MQTT_HOSTPORT = 1883
MQTT_USERNAME = None #"vbjsfwul"
MQTT_PASSWORD = None #"xottyHH5j9v2"
MQTT_TOPIC = "iot-1/d/%012x/evt/%s/json" % (get_mac(), "computer")

# Create message queue
queue = Queue(QUEUE_SIZE)

# Create and start event reporter
reporter = EventReporter(queue)
reporter.daemon = True
reporter.start()

# Create publishers
pb_mqtt = MQTTPublisher(
	name = "MQTT",
	queue_size = 100,
	callback = reporter.send_false_callback,
	topic = MQTT_TOPIC
)
if pb_mqtt.connect(MQTT_HOSTNAME, MQTT_HOSTPORT, MQTT_USERNAME, MQTT_PASSWORD):
	reporter.append_publisher(pb_mqtt)
	pb_mqtt.daemon = True
	pb_mqtt.start()

# Create and start virtual sensors
# Create Heartbeat "Sensor"
ls_vs = []
vs_heartbeat = HBVirtualSensor(
	queue,
	DeviceDescriptor("hb0"),
	interval = 10
)
if vs_heartbeat.connect():
	ls_vs.append(vs_heartbeat)

# Create PIR Motion Virtual Sensor
vs_pir = DummyPIRVirtualSensor(
	queue,
	DeviceDescriptor("pir0"),
#	gpio_pin = 17
)
if vs_pir.connect():
	ls_vs.append(vs_pir)

# Create Light Virtual Sensor
vs_light = DummyLightVirtualSensor(
	queue,
	DeviceDescriptor("light0"),
#	analog_port = 3,
	threshold = 400
)
if vs_light.connect():
	ls_vs.append(vs_light)

# Create Gas Virtual Sensor
vs_gas = DummyGasVirtualSensor(
	queue,
	DeviceDescriptor("gas0"),
#	analog_port = 0,
	threshold = 500
)
if vs_gas.connect():
	ls_vs.append(vs_gas)

# Dummy Sheeva Sensors
vs_temperature = DummyTemperatureVirtualSensor(
	queue,
	DeviceDescriptor("cel0"),
#	daemon_path = CEL_DAEMON_PATH,
	threshold = 24.0
)
if vs_temperature.connect():
	ls_vs.append(vs_temperature)

vs_csn = DummyCSNVirtualSensor(
	queue,
	DeviceDescriptor("accel"))
if vs_csn.connect():
	ls_vs.append(vs_csn)

# Start all the sensors
for vs_j in ls_vs:
	vs_j.daemon = True
	vs_j.start()

# Loop forever
while True:
	time.sleep(1)
