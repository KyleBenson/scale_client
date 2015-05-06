import json
import peewee

from scale_client.event_sinks.event_sink import EventSink

import logging
log = logging.getLogger(__name__)

class MySQLEventSink(EventSink):
	def __init__(self, broker, dbname, username, password):
		super(MySQLEventSink, self).__init__(broker)

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
		self._create_table()
		return True

	def _create_table(self):
		try:
			self.EventRecord.create_table()
			log.info("created table: "+ str(self.EventRecord._meta.db_table))
		except peewee.OperationalError:
			pass

	def on_start(self):
		self._try_connect()

	def encode_event(self, event):
		# If event is from database, update upload stamp
		if hasattr(event, "db_record"):
			table_id = event.db_record["table_id"]
			upload_time = event.db_record["upload_time"]
			encoded_event = self.EventRecord.update(
					upload_time = upload_time
				).where(self.EventRecord.id == table_id)
			return encoded_event

		# If event is NOT from database, insert into database
		geotag = None
		if "geotag" in event.data:
			geotag = event.data["geotag"]
		encoded_event = self.EventRecord(
				sensor=event.sensor,
				event=event.data["event"],
				priority=event.priority,
				timestamp=event.timestamp,
				geotag=geotag,
				value_json=json.dumps(event.data["value"])
			)
		return encoded_event
	
	def check_available(self, event):
		if self._db is None:
			#log.debug("not available")
			return self._try_connect()
		#log.debug("available")
		return True

	def send(self, encoded_event):
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

