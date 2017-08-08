import json
import peewee

from scale_client.event_sinks.mysql_event_sink import MySQLEventSink

import logging
log = logging.getLogger(__name__)

class MySQLClassifiedEventSink(MySQLEventSink):
	def __init__(self, broker, dbname, username, password, event_types=tuple(), **kwargs):
		super(MySQLClassifiedEventSink, self).__init__(broker, dbname, username, password, **kwargs)
		
		if type(event_types) != type([]):
			raise TypeError
		self._kls_types = {}

		# Create class objects for each event type
		for event_type in event_types:
			if event_type in self._kls_types:
				log.warning("duplicate item in list event_types")
				next
			try:
				self._kls_types[event_type] = self._create_kls(event_type)
			except TypeError, err:
				log.error(str(err))
	
	def _create_kls(self, event_type):
		if type(event_type) != type(""):
			raise TypeError

		class ClassifiedEventRecord(self.EventRecord):
			class Meta:
				database = None
				db_table = "type_" + event_type
		return ClassifiedEventRecord

	def _set_db(self, record_kls=None):
		if record_kls is None:
			for kls in self._kls_types:
				self._set_db(self._kls_types[kls])
			return
		super(MySQLClassifiedEventSink, self)._set_db(record_kls)

	def _create_table(self, record_kls=None):
		if record_kls is None:
			for kls in self._kls_types:
				self._create_table(self._kls_types[kls])
			return
		super(MySQLClassifiedEventSink, self)._create_table(record_kls)

	def encode_event(self, event):
		# If event is from database, ignore
		if "db_record" in event.metadata:
			return None

		# Filter other events
		et = event.event_type
		if not et in self._kls_types:
			return None

		# If event is NOT from database
		geotag = None
		if event.location:
			geotag = json.dumps(event.location)
		condition = None
		if event.condition:
			condition = json.dumps(event.condition)
		kls = self._kls_types[et]
		encoded_event = kls(
				sensor=event.sensor,
				event=event.event_type,
				priority=event.priority,
				timestamp=event.timestamp,
				geotag=geotag,
				value_json=json.dumps(event.data),
				condition=condition
			)
		return encoded_event
	
	def send_raw(self, encoded_event):
		if encoded_event is None:
			return False

		try:
			if isinstance(encoded_event, self.EventRecord):
				encoded_event.save()
				log.info("MySQL record saved to: " + str(encoded_event._meta.db_table))
				return False # to avoid influence on normal behavior
		except peewee.OperationalError, err:
			log.error(str(err))
			self._db = None
		except peewee.ProgrammingError, err:
			log.error(str(err))
			self._db = None
		return False

