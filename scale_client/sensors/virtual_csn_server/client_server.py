# coding=utf-8

"""
Server to handler creating and updating clients.

"""
import random
import hashlib

from scale_client.sensors.virtual_csn_server import api_handler
import util
from messages import client_messages_pb2


CLIENT_FIELD_OPTIONAL = [
    'name', 'location_source_type', 'location_description', 'floor',
    'building', 'mobility_type', 'software_version', 'operating_system',
    'uuid', 'legacy_identifier',
]
SENSOR_FIELD_OPTIONAL = [
    'model', 'serial', 'calibrated', 'units',
    'num_samples', 'sample_window_size'
]
KV_HINT_TO_TYPE = {
    's': 'string_value',
    'd': 'double_value',
    'l': 'long_value',
    'b': 'bool_value',
}
KV_TYPE_TO_HINT = {v: k for k, v in KV_HINT_TO_TYPE.items()}


class CreateHandler(api_handler.ProtobufHandler):
    """
    Handler responsible for all new client registrations.

    """

    REQUEST_OBJ = client_messages_pb2.ClientCreateMessage
    RESPONSE_OBJ = client_messages_pb2.ClientCreateResponse

    def post_pb(self):
        """
        Create a new `Client` object using the provided metadata.

        Exception raised if sensors without types are described.

        """
        current_time = util.system_time()

        self.response_pb.client_id = random.getrandbits(64)
        self.response_pb.client_secret = self.generate_secret(current_time)

        self.write_response()
	print('\n\nCreateHandler request')
	print(self.request_pb)
	print('\n\nCreateHandler response')
	print(self.response_pb)

    def generate_secret(environment, current_time):
        """
    	Create a random value using the system environment and time as a seed.

    	Parameters
    	----------
    	environment : webapp2.environment
        Used to provide additional entropy when hashing with the system time.

    	Notes
    	-----
    	This generator should be sufficiently random for our limited purposes, but
    	PyCrypto_ is available as a Python 2.7 library on App Engine if additional
    	security is desired.

    	.. _PyCrypto: https://www.dlitz.net/software/pycrypto/

    	"""
    	secret_hash = hashlib.sha256('{}/{}'.format(
                                 environment, util.date_format(current_time)))
    	return secret_hash.hexdigest()


class UpdateHandler(api_handler.ProtobufHandler):
    """
    Handler responsible for updating client metadata.

    """

    REQUIRE_CLIENT = True
    REQUEST_OBJ = client_messages_pb2.ClientUpdateMessage
    RESPONSE_OBJ = client_messages_pb2.ClientUpdateResponse

    def post_pb(self, client_id_str=None):
        """
        Calls `perform_update` and returns newly generated `Sensor` ids.

        """
	if self.request_pb.new_sensors:
            self.response_pb.sensor_ids.append(0)

        self.write_response(
        	'No changes to client requested or all properties are '
                'already at their desired values.')
	print('\n\nUpdateHanler Request')
	print(self.request_pb)
	print('\n\nUpdateHanler Response')
	print(self.response_pb)

class MetadataHandler(api_handler.ProtobufHandler):
    """
    Handler to send `Client` and `Sensor` metadata to client when requested.

    """

    REQUIRE_CLIENT = True
    REQUEST_OBJ = client_messages_pb2.ClientMetadataRequest
    RESPONSE_OBJ = client_messages_pb2.ClientMetadataResponse

    def post_pb(self, client_id_str=None):
	self.response_pb.client_data.latitude =  0.0

        self.response_pb.client_data.longitude =  0.0
	#self.response_pb.client_data.location_source_type = 'SERVER_DEFAULT'
	#self.response_pb.client_data.mobility_type = 'DESKTOP'
	#self.response_pb.client_data.software_version = '2.2b3'
	#self.response_pb.client_data.operating_system = 'Linux'

	#self.response_pb.sensor_data.sensor_id = 0
  	#self.response_pb.sensor_data.sensor_type = 'ACCELEROMETER_3_AXIS'
  	#self.response_pb.sensor_data.model = 'Phidgets 1056'
  	#self.response_pb.sensor_data.serial = 252391
  	#self.response_pb.sensor_data.calibrated = 'true'
  	#self.response_pb.sensor_data.units = 'g'
  	#self.response_pb.sensor_data.num_samples = 50
  	#self.response_pb.sensor_data.sample_window_size = 1

        self.write_response()

	print('\n\nmetadata request ')
	print(self.request_pb)
	print('\n\nmetadata response ')
	print(self.response_pb)

'''
class KeyValueHandler(api_handler.ProtobufHandler):
    """
    Handler for metadata stored by the client software in the `Client` object.

    """

    REQUIRE_CLIENT = True
    REQUEST_OBJ = client_messages_pb2.ClientKeyValueRequest
    RESPONSE_OBJ = client_messages_pb2.ClientKeyValueResponse

    def post_pb(self, client_id_str):
        """Retrieve keys identified in `request_pb` for specified `Client`."""
        client = self.get_and_verify_client(client_id_str)
        for key in self.request_pb.client_keys:
            kv_msg = self.response_pb.client_data.add()
            kv_msg.key = key
            try:
                type_hint, value = client.keyvalue[key]
            except (KeyError, TypeError):
                raise api_handler.InvalidRequest(
                    'Key "{}" does not exist.'.format(key))
            setattr(kv_msg, KV_HINT_TO_TYPE[type_hint], value)
        self.write_response()


class EditTokenHandler(api_handler.ProtobufHandler):
    """
    Handler to return URLs that can be used to edit clients without auth.

    """

    REQUIRE_CLIENT = True
    REQUEST_OBJ = client_messages_pb2.ClientEditorTokenRequest
    RESPONSE_OBJ = client_messages_pb2.ClientEditorTokenResponse

    def post_pb(self, client_id_str=None):
        """Generate a client editor token and return it."""
        current_time = util.system_time()
        url = self.client_transaction(
            self._generate_token, client_id_str, current_time)
        self.response_pb.editor_url = url
        self.write_response()

    def _generate_token(self, client, current_time):
        """Generate a token for the provided client."""
        token = models.client.generate_secret(None, current_time)
        url = '{}#/clients/{}/{}?token={}'.format(
            self.uri_for('not-found', _scheme='https', path=''),
            self.namespace, client.key.id(), token)
        client.editor_token = token
        client.editor_expiry = current_time + datetime.timedelta(minutes=30)
        client.put()
        return url
'''
