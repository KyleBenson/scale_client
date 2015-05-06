import json
import peewee

from scale_client.event_sinks.mysql_event_sink import MySQLEventSink

import logging
log = logging.getLogger(__name__)

class MySQLClassifiedEventSink(MySQLEventSink):
	def __init__(self, broker, dbname, username, password, event_types=[]):
		super(MySQLClassifiedEventSink, self).__init__(broker, dbname, username, password)
		
		if type(event_types) != type([]):
			raise TypeError
		self._kls_types = {}

		# Create class objects for each event type
		for event_type in event_types:
			if event_type in self._kls_types:
				log.info("duplicate item in list event_types")
				next
			try:
				self._kls_types[event_type] = self._create_kls(event_type)
			except TypeError:
				log.error("incorrect item in list event_types")
	
	def _create_kls(self, event_type):
		if type(event_type) != type(""):
			raise TypeError

		class ClassifiedEventRecord(MySQLEventSink.EventRecord):
			class Meta:
				database = None
				db_table = event_type
		return ClassifiedEventRecord

	def _set_db(self, record_kls=None):
		if record_kls is None:
			for kls in self._kls_types:
				self._set_db(kls)
			return
		super(MySQLClassifiedEventSink, self)._set_db(self, record_kls)

	def _create_table(self, record_kls=None):
		if record_kls is None:
			for kls in self._kls_types:
				self._create_table(kls)
			return
		super(MySQLClassifiedEventSink, self)._create_table(self, record_kls)

	def encode_event(self, event):
		#TODO: implement
		raise NotImplementedError
	
