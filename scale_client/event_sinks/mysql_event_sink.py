import json
import peewee

from scale_client.event_sinks.event_sink import EventSink

import logging
log = logging.getLogger(__name__)

class MySQLEventSink(EventSink):
	def __init__(self, broker, dbname, username, password, **kwargs):
		super(MySQLEventSink, self).__init__(broker, **kwargs)

		self._dbname = dbname
		self._username = username
		self._password = password

		self._db = None

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
		self._set_db()
		if self._db is None:
			return False
		self._create_table()
		return True
	
	def _set_db(self, record_kls=None):
		if record_kls is None:
			self._set_db(self.EventRecord)
			return
		record_kls._meta.database = self._db
	
	def _create_table(self, record_kls=None):
		if record_kls is None:
			self._create_table(self.EventRecord)
			return
		try:
			record_kls.create_table()
			log.info("created table: "+ str(record_kls._meta.db_table))
		except peewee.OperationalError:
			pass
	
	def on_start(self):
		self._try_connect()

	def encode_event(self, event):
		# If event is from database, update upload stamp
		if "db_record" in event.metadata:
			table_id = event.metadata['db_record']["table_id"]
			upload_time = event.metadata['db_record']["upload_time"]
			encoded_event = self.EventRecord.update(
					upload_time = upload_time
				).where(self.EventRecord.id == table_id)
			return encoded_event

		# If event is NOT from database, insert into database
		geotag = None
		if event.location:
			geotag = json.dumps(event.location)
		condition = None
		if event.condition:
			condition = json.dumps(event.condition)
		encoded_event = self.EventRecord(
				sensor=event.sensor,
				event=event.event_type,
				priority=event.priority,
				timestamp=event.timestamp,
				geotag=geotag,
				value_json=json.dumps(event.data),
				condition=condition
			)
		return encoded_event
	
	def check_available(self, event):
		if self._db is None:
			#log.debug("not available")
			return self._try_connect()
		#log.debug("available")
		return True

	def send_raw(self, encoded_event):
		try:
			if isinstance(encoded_event, self.EventRecord):
				encoded_event.save()
				log.info("MySQL record saved to " + str(self.EventRecord._meta.db_table))
				return True
			elif isinstance(encoded_event, peewee.UpdateQuery):
				encoded_event.execute()
				log.debug("MySQL record updated")
				return True
		except peewee.OperationalError, err:
			log.error(str(err))
			self._db = None
		except peewee.ProgrammingError, err:
			log.error(str(err))
			self._db = None
		return False

