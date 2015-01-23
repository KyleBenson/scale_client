from Queue import Queue
import peewee
from peewee import *
import sys
from scale_client.publishers.publisher import Publisher

class MySQLPublisher(Publisher):
	def __init__(self, name, queue_size, callback):
		Publisher.__init__(self, name, queue_size, callback)
		self._db = None

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

	def send(self, event): #XXX: Identical overwrite seems useless
		self._queue.put(event)

	def publish(self, encoded_event):
		if isinstance(encoded_event, peewee.UpdateQuery):
			encoded_event.execute()
			# print "Update query handled."
			return True
		elif isinstance(encoded_event, self.EventRecord):
			encoded_event.save()
			return True
		print >>sys.stderr, "Publisher failed to identify type of encoded event."
		return False

	def encode_event(self, event):
		import json

		if isinstance(event, tuple):
			tableid, upldstamp = event
			encoded_event = self.EventRecord.update(
				upldstamp = upldstamp
			).where(self.EventRecord.id == tableid)
			# print "Update query for record %d" % tableid
			if upldstamp:
				print "Delivered record: %d" % tableid
			else: #None
				print "Undelivered record: %d" % tableid
			return encoded_event

		gpstamp = None
		if hasattr(event, "gpstamp"):
			gpstamp = json.dumps(event.gpstamp)

		encoded_event = MySQLPublisher.EventRecord(
			sensor = event.sensor,
			msg = json.dumps(event.msg),
			priority = event.priority,
			timestamp = event.timestamp,
			gpstamp = gpstamp
		)
		return encoded_event	
	
	def check_available(self, event):
		return True	

	def update_upldstamp(self, tableid, upldstamp):
		self._queue.put((tableid, upldstamp))
