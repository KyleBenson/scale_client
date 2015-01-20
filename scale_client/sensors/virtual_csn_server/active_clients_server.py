# coding=utf-8

"""
Server for changing activity status and location of clients.

"""

from scale_client.sensors.virtual_csn_server import task_handler


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
