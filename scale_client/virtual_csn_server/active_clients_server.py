# coding=utf-8

"""
Server for changing activity status and location of clients.

"""

import datetime
import logging

import task_handler
import util


#EPSILON = 0.00001
#QUEUE_NAME = 'activeclients'

class SetActiveHandler(task_handler.TaskHandler):

    def post(self, namespace=None, client_id_str=None):
	#print('SetActiveHandler')
	pass
class ChangeHandler(task_handler.TaskHandler):

    def post(self, namespace=None, geostr=None, active_str=None):
	#print('changeHandler')
	pass

class GeocellHandler(task_handler.TaskHandler):

    def post(self, namespace=None, geostr=None, active_str=None):
	#print('GeocellHandler')
	pass

class BackupHandler(task_handler.TaskHandler):

    def post(self, namespace=None, geostr=None, action=None):
	#print('BackupHandler')
	pass
