import time
import iwlib
from iwlib import iwlist
#from scale_client.core.sensed_event import SensedEvent
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

import logging
log = logging.getLogger(__name__)

class IWListVirtualSensor(ThreadedVirtualSensor):
	def __init__(self, broker, device=None, interval = 4, if_name = None):
		super(IWListVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._interval = interval
		self._if_name = if_name # Interface device name, for example: wlan0

	def get_type(self):
		return "iwlist_scan"

	def on_start(self):
		try:
			iwlist.scan(self._if_name)
		except TypeError:
			log.error("failed to start because of TypeError")
			return False
		except OSError:
			log.error("failed to start because of OSError")
			return False
		
		super(IWListVirtualSensor, self).on_start()

	def scan(self):
		return iwlist.scan(self._if_name)

	def _get_bssid(self, ap):
		if "Access Point" in ap:
			return ap["Access Point"]
		elif "Cell" in ap:
			return ap["Cell"]
		log.info("BSSID field not found for ESSID: %s" % ap["ESSID"])
		return None
	
	def _do_sensor_read(self):
		log.debug("%s reading sensor data..." % self.get_type())

		ap_list = self.scan()
		timestamp = time.time()
		event_list = []
		for ap in ap_list:
			data = {
					"essid": ap["ESSID"],
					"bssid": self._get_bssid(ap),
					"mode": ap["Mode"].lower(),
					"noise": ap["stats"]["noise"],
					"level": ap["stats"]["level"],
					"quality": ap["stats"]["quality"]
				}
			event = self.make_event_with_raw_data(data)
			event.timestamp = timestamp
			event_list.append(event)

		for event in event_list:
			if event is None:
				continue
			if self.policy_check(event):
				self.publish(event)
	
	def policy_check(self, data):
		return True

"""
	def policy_check(self, data):
		ls_ap = data
		ls_event = []
		timestamp = time.time()

		for ap in ls_ap:
			ls_event.append(
				SensedEvent(
					sensor = self.device.device,
					msg = {
						"event": self.get_type(),
						"value": ap,
						"condition": {}
					},
					priority = 9,
					timestamp = timestamp
				)
			)
		return ls_event
"""

