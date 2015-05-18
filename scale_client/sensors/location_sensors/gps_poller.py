#!/usr/bin/python

import threading
from threading import Thread
import time
from datetime import datetime
from gps import *
from socket import error as SocketError
import sys
import subprocess
import _strptime

class GPSPoller(Thread):
	def __init__(self, retry = 2.0):
		Thread.__init__(self)
		self._state = GPSPoller._State.S_INIT
		self._retry = retry
		self._gpsd = None
	
	class _State:
		S_INIT = -1
		F_GPSD = -2
		S_RUNNING = 0
	
	class _GPSWatchDog(Thread):
		def __init__(self, poller):
			Thread.__init__(self)
			self._poller = poller

		V_DAEMON_FAIL = 5.0
		DELAY_BASIC = 2.0
		DELAY_LIMIT = 60.0

		def run(self):
			ptime_last = None
			timer = None
			delay = GPSPoller._GPSWatchDog.DELAY_BASIC
			while True:
				if self._poller.has_gpsd():
					ptime_this = self._poller.ptime()
					if ptime_this == 0.0 or ptime_this == ptime_last:
						if not timer: # Should not occur
							timer = time.time()
						if time.time() - timer > GPSPoller._GPSWatchDog.V_DAEMON_FAIL:
							ptime_last = None
							timer = None

							# Restart GPS daemon service
							print "GPS is not responding. Daemon will restart in %d seconds." % delay
							if delay > GPSPoller._GPSWatchDog.V_DAEMON_FAIL:
								time.sleep(delay - GPSPoller._GPSWatchDog.V_DAEMON_FAIL)
							if delay < GPSPoller._GPSWatchDog.DELAY_LIMIT / 2:
								delay *= 2
							else: delay = GPSPoller._GPSWatchDog.DELAY_LIMIT
							subprocess.call("service gpsd restart", shell = True)
					else:
						ptime_last = ptime_this
						timer = time.time()
						delay = GPSPoller._GPSWatchDog.DELAY_BASIC
					time.sleep(1)

	def run(self):
		watch_dog = GPSPoller._GPSWatchDog(self)
		watch_dog.daemon = True
		watch_dog.start()
		while True:
			if self._state == GPSPoller._State.S_INIT:
				try:
					self._gpsd = gps(mode = WATCH_ENABLE)
					self._state = GPSPoller._State.S_RUNNING
				except SocketError:
					self._state = GPSPoller._State.F_GPSD
			elif self._state == GPSPoller._State.F_GPSD:
				time.sleep(self._retry)
				self._state = GPSPoller._State.S_INIT
			elif self._state == GPSPoller._State.S_RUNNING:
				try:
					self._gpsd.next()
				except StopIteration:
					self._state = GPSPoller._State.F_GPSD
	
	def lat(self):
		return self._gpsd.fix.latitude
	
	def lon(self):
		return self._gpsd.fix.longitude
	
	def alt(self):
		return self._gpsd.fix.altitude
	
	# Ground speed (m/sec)
	def speed(self):
		return self._gpsd.fix.speed
	
	# Climb rate (m/sec)
	def climb(self):
		return self._gpsd.fix.climb

	# Course over ground from true north (deg)
	def track(self):
		return self._gpsd.fix.track
	
	# UTC time string
	def _utc(self):
		return self._gpsd.utc
	
	def ptime(self):
		dtime = None
		try:
			dtime = datetime.strptime(self._utc(), "%Y-%m-%dT%H:%M:%S.%fZ")
		except ValueError:
			pass
		except TypeError:
			pass
		if dtime:
			zone = 0
			if time.localtime().tm_isdst == 1:
				zone = time.altzone
			elif time.localtime().tm_isdst == 0:
				zone = time.timezone
			return time.mktime(dtime.timetuple())+dtime.microsecond/1.0e+6-zone
		return 0.0

	# Estimated longitude error (m)
	def epx(self):
		return self._gpsd.fix.epx

	# Estimated latitude error (m)
	def epy(self):
		return self._gpsd.fix.epy

	# Estimated vertical error (m/sec)
	def epv(self):
		return self._gpsd.fix.epv
	
	# Estimated speed error (m/sec)
	def eps(self):
		return self._gpsd.fix.eps

	# Estimated course error (deg)
	def epd(self):
		return self._gpsd.fix.epd

	# Estimated time-stamp error (sec)
	def ept(self):
		return self._gpsd.fix.ept

	# Fix mode
	def mode(self):
		return self._gpsd.fix.mode

	MODE_STR = {
		0: "NO DATA",
		1: "NO FIX",
		2: "2D FIX",
		3: "3D FIX"
	}

	# Satellites
	def sat(self):
		return self._gpsd.satellites
	
	def has_gpsd(self):
		if not self._gpsd:
			return False
		return True

	def get_dict(self):
		if not self.has_gpsd():
			return None
		sat = self.sat()
		return {
			"lat": self.lat(),
			"lon": self.lon(),
			"alt": self.alt(),
			"speed": self.speed(),
			"climb": self.climb(),
			"track": self.track(),
			"ptime": self.ptime(),
			"epx": self.epx(),
			"epy": self.epy(),
			"epv": self.epv(),
			"eps": self.eps(),
			"epd": self.epd(),
			"ept": self.ept(),
			"mode": self.mode(),
			"sat": {
				"total": len(sat)
			}
		}

MAIN_SLEEP = 1

if __name__ == "__main__":
	poller = GPSPoller()
	poller.daemon = True
	poller.start()
	while True:
		print poller.get_dict()
		time.sleep(MAIN_SLEEP)
