import threading
import os
import re
import subprocess
from threading import Thread
#from virtual_csn_server.main import *
from Queue import Queue
from virtual_sensor import VirtualSensor
from sensed_event import SensedEvent

SCALE_VS_MAGIC_LN = r"\$\$\$_SCALE_VS_MAGIC_LN_\$\$\$"


class CSNVirtualSensor(VirtualSensor):
	def __init__(self, queue, device):
		VirtualSensor.__init__(self, queue, device)
		self._reading_regexp = re.compile(r'.*readings: ([\-\+]?[0-9]*(\.[0-9]+)?)') 
		self._magic_ln_regexp = re.compile(SCALE_VS_MAGIC_LN)
		self._result = None

	def type(self):
	#	return "CSN Accelerometer"
		return "SCALE_Seismic_Sheeva"

	def connect(self):
		self._result = subprocess.Popen(
			["/root/SmartAmericaSensors/scale_client/virtual_csn_server/main.py"],
			shell = True,
			stdout = subprocess.PIPE
		)
		return True

	def read(self):
		#pipe_file = open(FIFO_FILE, 'r')
		
		readings = []
		for ln in iter(self._result.stdout.readline, ''):
			print ("Line: " + ln.rstrip())
			magic_ln_match = self._magic_ln_regexp.match(ln.rstrip())
			if magic_ln_match:
			#	print ("Magic ln match")
				break;
			else:
				reading_match = self._reading_regexp.match(ln)
				if reading_match:
			#		print ("Reading match")
					readings.append(float(reading_match.group(1)))

		#pipe_file.close()
		return readings

	def policy_check(self, data):
		ls_event = []
		if len(data) < 3:
			return ls_event
		ls_event.append(
			SensedEvent(
				sensor = self.device.device,
				msg = {
					"event": "SCALE_pick_detected_Sheeva",
					"value": data,
					"condition": {}
				},
				priority = 5
			)
		)
		return ls_event
