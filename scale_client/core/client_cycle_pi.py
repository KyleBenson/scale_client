#!/usr/bin/python

import threading
import time
import urllib2
import socket
import sys
from threading import Thread
from Queue import Queue
from uuid import getnode as get_mac

#XXX: Hard-coded path to find SCALE modules
sys.path.append("/home/charles/scale_cycle")

from scale_client.core.device_descriptor import DeviceDescriptor
from scale_client.core.event_reporter import EventReporter
#from publisher import Publisher
#from virtual_sensor import VirtualSensor

#from gpio_virtual_sensor import GPIOVirtualSensor
#from analog_virtual_sensor import AnalogVirtualSensor
#from pir_virtual_sensor import PIRVirtualSensor 
#from light_virtual_sensor import LightVirtualSensor
#from gas_virtual_sensor import GasVirtualSensor
from scale_client.sensors.heartbeat_virtual_sensor import HeartbeatVirtualSensor as HBSensor
from scale_client.sensors.iwlist_scan_virtual_sensor import IWListScanVirtualSensor as IWLSensor
from scale_client.sensors.gps.gps_poller import *
from scale_client.sensors.gps.gp_sensed_event import GPSensedEvent
from scale_client.sensors.gps.gps_heartbeat_virtual_sensor import GPSHeartbeatVirtualSensor as GPSHBSensor
from scale_client.sensors.gps.gps_iwlist_scan_virtual_sensor import GPSIWListScanVirtualSensor as GPSIWLSensor
from scale_client.sensors.mysql_virtual_sensor import MySQLVirtualSensor

from scale_client.publishers.mqtt_publisher import MQTTPublisher
from scale_client.publishers.mysql_publisher import MySQLPublisher
#from text_writer_publisher import TextWriterPublisher

QUEUE_SIZE = 4096

MQTT_HOSTNAME = "dime.smartamerica.io"
MQTT_HOSTPORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None

# MQTT publisher will fill in the "%s" below
#MQTT_TOPIC = "iot-1/d/%012x/evt/%s/json" % (get_mac(), "%s") 
MQTT_TOPIC = "iot-test/d/%012x/evt/%s/json" % (get_mac(), "%s") 

#TEXT_WR_PATH = "/var/scale_log/cycle_%d/" % (int(time.time()))
IW_NAME = "wlan0"

MYSQL_DB = "scale_cycle"
MYSQL_USER = "scale_usr"
MYSQL_PASSWD = "123456"

# Create message queue
queue = Queue(QUEUE_SIZE)

# Create and start event reporter
reporter = EventReporter(queue)
reporter.daemon = True
reporter.start()

# Create GPS poller
gps_poller = GPSPoller()
gps_poller.daemon = True
gps_poller.start()
GPSensedEvent.set_poller(gps_poller)

# Create publishers

pb_mqtt = MQTTPublisher(
	name = "MQTT",
	queue_size = 100,
	callback = reporter.send_callback,
	topic = MQTT_TOPIC
)
if pb_mqtt.connect(MQTT_HOSTNAME, MQTT_HOSTPORT, MQTT_USERNAME, MQTT_PASSWORD):
	reporter.append_publisher(pb_mqtt)
	pb_mqtt.daemon = True
	pb_mqtt.start()
"""
pb_text = TextWriterPublisher(
	name = "Text",
	queue_size = 64,
	callback = reporter.send_callback
)
if pb_text.connect(TEXT_WR_PATH):
	reporter.append_publisher(pb_text)
	pb_text.daemon = True
	pb_text.start()
"""

pb_mysql = MySQLPublisher(
	name = "MySQL",
	queue_size = 64,
	callback = reporter.send_callback
)
if pb_mysql.connect(MYSQL_DB, MYSQL_USER, MYSQL_PASSWD):
	reporter.append_publisher(pb_mysql)
	pb_mysql.daemon = True
	pb_mysql.start()

# Create and start virtual sensors
# Create Heartbeat "Sensor"
ls_vs = []
vs_heartbeat = HBSensor(
	queue,
	DeviceDescriptor("hb0"),
	interval = 60
)
if vs_heartbeat.connect():
	ls_vs.append(vs_heartbeat)

# Create GPS Heartbeat "sensor"
vs_t = GPSHBSensor(
	queue,
	DeviceDescriptor("hb1"),
	interval = 2
)
if vs_t.connect():
	ls_vs.append(vs_t)

# Create iwlist scan sensor
vs_t = IWLSensor(
	queue,
	DeviceDescriptor("iwls0"),
	if_name = IW_NAME
)
if vs_t.connect():
	ls_vs.append(vs_t)

vs_t = GPSIWLSensor(
	queue = queue,
	device_sensor = DeviceDescriptor("iwls1"),
	interval = 1.5,
	if_name = IW_NAME
)
if vs_t.connect():
	ls_vs.append(vs_t)

vs_t = MySQLVirtualSensor(
	queue = queue,
	device = DeviceDescriptor("mysql0"),
	interval = 1 
)
if vs_t.connect(MYSQL_DB, MYSQL_USER, MYSQL_PASSWD):
	ls_vs.append(vs_t)

# Start all the sensors
for vs_j in ls_vs:
	vs_j.daemon = True
	vs_j.start()

# Loop forever
while True:
	time.sleep(1)
