from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import json
import time
import peewee
from threading import Lock

import logging
log = logging.getLogger(__name__)

class MySQLMaintainer(Application):
	def __init__(self, broker, dbname, username, password, interval=10, cleanup=43200):
		super(MySQLMaintainer, self).__init__(broker)

		self._interval = interval
		self._dbname = dbname
		self._username = username
		self._password = password

		self._db = None
		self._neta = None
		self._puba = None
		self._db_lock = Lock()
		self._clean_timer = None
		self._clean_timeout = cleanup
	
	class EventRecord(peewee.Model):
		class Meta:
			database = None
			db_table = "events"

		sensor = peewee.CharField(max_length = 16)
		event = peewee.CharField(max_length = 64)
		priority = peewee.IntegerField()
		timestamp = peewee.DoubleField()
		geotag = peewee.TextField(null = True)
		value_json = peewee.TextField()
		upload_time = peewee.DoubleField(null = True)
		condition = peewee.TextField(null = True)
	
	def _try_connect(self):
		self._db = peewee.MySQLDatabase(
				self._dbname,
				user=self._username,
				passwd=self._password
			)
		try:
			self._db.connect()
		except peewee.OperationalError, err:
			self._db = None
			log.error(str(err))
		self.EventRecord._meta.database = self._db
		if self._db is None:
			return False
		return True
	
	def on_start(self):
		self._try_connect()
		#self._clean_up()
		if self._interval is None:
			return
		self.timed_call(self._interval, MySQLMaintainer._cron, repeat=True)

	def _cron(self):
		if self._db is None:
			if not self._try_connect():
				return

		# Clean up
		if self._clean_timer is None or self._clean_timer + self._clean_timeout < time.time():
			self._clean_up()
			self._clean_timer = time.time()

		# Check for available publishers
		# Will not check for Internet access
		if not self._puba:
			log.info("no available publisher reported")
			return

		res_list = None
		id_list = []
		event_list = []
		self._db_lock.acquire()
		try:
			res_list = self.EventRecord.select().where(self.EventRecord.upload_time == None)
			for rec in res_list:
				structured_data = {
						"event": rec.event,
						"value": json.loads(rec.value_json)
					}
				if rec.geotag is not None:
					structured_data["geotag"] = json.loads(rec.geotag)
				if rec.condition is not None:
					structured_data["condition"] = json.loads(rec.condition)
				event = SensedEvent(
						rec.sensor,
						structured_data,
						rec.priority,
						timestamp = rec.timestamp
					)
				event.db_record = {
						"table_id": rec.id,
						"upload_time": rec.upload_time # should be None
					}
				id_list.append(rec.id)
				event_list.append(event)
		except peewee.OperationalError, err:
			log.error(str(err))
			self._db = None
			return
		except peewee.ProgrammingError, err:
			log.error(str(err))
			self._db = None
			return
		finally:
			self._db_lock.release()

		log.info("fetched %d record(s)" % len(id_list))
		if len(id_list) < 1:
			return
		
		self._db_lock.acquire()
		try:
			self.EventRecord.update(
					upload_time = -4.0
				).where(self.EventRecord.id << id_list).execute()
		except peewee.OperationalError, err:
			log.error(str(err))
			self._db = None
			return
		finally:
			self._db_lock.release()

		for event in event_list:
			if event is None:
				continue
			self.publish(event)
	
	def on_event(self, event, topic):
		et = event.get_type()
		ed = event.get_raw_data()

		if et == "internet_access":
			self._neta = ed
		elif et == "publisher_state":
			self._puba = ed

	def _clean_up(self):
		"""
		This method cleans up the `events` table for already-uploaded events.
		Records in database have initial `upload_time` as None.
		A successful publish of record will update `upload_time` for the event.
		"""
		# currently only called once at start up
		#XXX: should be called whlie running for longer runs of client

		if self._db is None:
			return
		self._db_lock.acquire()
		try:
			# Delete uploaded events
			self.EventRecord.delete().where(
					self.EventRecord.upload_time > 0.0
				).execute()

			# Delete unexpected events: loaded but not processed
			self.EventRecord.delete().where(
					self.EventRecord.upload_time < 0.0 and self.EventRecord.timestamp < time.time() - 300
				).execute()
			log.info("MySQL database cleaned up")
		except peewee.OperationalError, err:
			log.error(str(err))
			self._db = None
		except peewee.ProgrammingError, err:
			log.error(str(err))
			self._db = None
		finally:
			self._db_lock.release()

