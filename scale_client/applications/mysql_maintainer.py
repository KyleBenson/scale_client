from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import json
import peewee
import logging
log = logging.getLogger(__name__)

class MySQLMaintainer(Application):
	def __init__(self, broker, dbname, username, password, interval=10):
		super(MySQLMaintainer, self).__init__(broker)

		self._interval = interval
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
		return True
	
	def on_start(self):
		if self._interval is None:
			return
		self._cron()
		self.timed_call(self._interval, MySQLMaintainer._cron, repeat=True)

	def _cron(self):
		if self._db is None:
			if not self._try_connect():
				return

		#TODO: Check for Internet access

		res_list = None
		try:
			res_list = self.EventRecord.select().where(self.EventRecord.upload_time == None)
		except peewee.OperationalError:
			log.debug("table is not ready")
		if res_list is None:
			return
		
		id_list = []
		event_list = []
		for rec in res_list:
			structured_data = {
					"event": rec.event,
					"value": json.loads(rec.value_json)
				}
			if rec.geotag is not None:
				structured_data["geotag"] = rec.geotag
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
		log.info("fetched %d record(s)" % len(id_list))
		if len(id_list) < 1:
			return
		
		try:
			self.EventRecord.update(
					upload_time = -4.0
				).where(self.EventRecord.id << id_list).execute()
		except peewee.OperationalError:
			log.debug("unable to update table, will not publish")
			return

		for event in event_list:
			if event is None:
				continue
			self.publish(event)
