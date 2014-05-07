import threading
import os
import re
import subprocess
from threading import Thread
from virtual_csn_server.main import *
from Queue import Queue
from virtual_sensor import VirtualSensor
from sensed_event import SensedEvent

FIFO_FILE = "/var/run/scale_vs_csn.fifo"
SCALE_VS_MAGIC_LN = "$$$_SCALE_VS_MAGIC_LN_$$$"


class CsnVirtualSensor(VirtualSensor):
	def __init__(self, queue, device):
		VirtualSensor.__init__(self, queue, device)
		self._reading_regexp = re.compile(r'.*readings: ([\-\+]?[0-9]*(\.[0-9]+)?)') 
		self._magic_ln_regexp = re.compile(SCALE_VS_MAGIC_LN)

	def type(self):
		return "CSN Accelerometer"

	def connect(self):
		try:
			os.mkfifo(FIFO_FILE)
		except OSError, e:
			print "Failed to create FIFO between SCALE and CSN Server: %s" % e
		#	pass
			return False
	#	server_thread = Thread(target = main)
	#	server_thread.daemon = True
	#	server_thread.start()
		subprocess.Popen(
			["/root/SmartAmericaSensors/scale_client/virtual_csn_server/main.py"],
		)
		return True

	def read(self):
		pipe_file = open(FIFO_FILE, 'r')
		readings = []
		for ln in pipe_file:
			magic_ln_match = self._magic_ln_regexp.match(ln.rstrip())
			if magic_ln_match:
				break;
			else:
				reading_match = self._reading_regexp.match(ln)
				if reading_match:
					readings.append(reading_match.group(1))

		pipe_file.close()
		return readings

	def policy_check(self, data):
		ls_event = []
		if len(data) < 3:
			return ls_event
		readings_line = data[0]+', '+data[1]+', '+data[2]
		ls_event.append(
			SensedEvent(
				sensor = self.device.device,
				msg = "Pick Detected: " + readings_line,
				priority = 70
			)
		)
		return ls_event
