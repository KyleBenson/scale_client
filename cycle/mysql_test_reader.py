#!/usr/bin/python

import peewee
from peewee import *
import sys

MYSQL_DB = "scale_cycle"
MYSQL_USER = "scale_usr"
MYSQL_PASSWD = "123456"

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

db = MySQLDatabase(MYSQL_DB, user = MYSQL_USER, passwd = MYSQL_PASSWD)
try:
	db.connect()
except OperationalError, err:
	print err
	exit(-1)

EventRecord._meta.database = db
res = EventRecord.select()
count = res.wrapped_count()
print "Fetched %d record(s)." % count
db.close()
