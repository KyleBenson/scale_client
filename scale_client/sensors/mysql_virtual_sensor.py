import peewee
from peewee import *
import sys
import time
import urllib2
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.sensors.gps.gp_sensed_event import GPSensedEvent

class MySQLVirtualSensor(VirtualSensor):
	def __init__(self, queue, device, interval = 1):
		VirtualSensor.__init__(self, queue, device)
		self._db = None
		self._interval = interval

	class EventRecord(peewee.Model):
		class Meta:
			database = None
			db_table = "events"

		sensor = peewee.CharField(max_length = 32)
		msg = peewee.TextField()
		priority = peewee.IntegerField()
		timestamp = peewee.DoubleField()
		gpstamp = peewee.TextField(null = True)
		upldstamp = peewee.DoubleField(null = True)

	def get_type(self):
		return "mysql_db"

	def connect(
		self,
		dbname,
		username,
		password
	):
		self._db = MySQLDatabase(dbname, user = username, passwd = password)
		try:
			self._db.connect()
		except peewee.OperationalError, err:
			print >>sys.stderr, "MySQL failure: " + str(err)
			return False
		self.EventRecord._meta.database = self._db
		try:
			self.EventRecord.create_table()
			print >>sys.stderr, "Creating table: " + str(self.EventRecord._meta.db_table)
		except peewee.OperationalError:
			self._db = None
		return True

	def read(self):
		res = None
		has_network = False
		while res is None or res.wrapped_count() < 1 or has_network == False:
			# time.sleep(self._interval)
			try:
				response = urllib2.urlopen('http://www.google.com', timeout = 2)
				has_network = True
			except urllib2.URLError:
				has_network = False
				time.sleep(self._interval)
				next
			res = self.EventRecord.select().where(self.EventRecord.upldstamp == None)
		# 	count = res.wrapped_count() 
		# print "Fetched %d record(s)." % count
		return res

	def policy_check(self, data):
		import json

		ls_event = []
		ls_id = []
		for rec in data:
			ls_event.append(
				GPSensedEvent(
					sensor = rec.sensor,
					msg = json.loads(rec.msg),
					priority = rec.priority,
					timestamp = rec.timestamp,
					gpstamp = rec.gpstamp,
					dbtableid = rec.id,
					upldstamp = rec.upldstamp
				)
			)
			ls_id.append(rec.id)
		self.EventRecord.update(
			upldstamp = 0.0
		).where(self.EventRecord.id << ls_id).execute()
		print "Fetched %d record(s)." % len(ls_id)
		return ls_event
