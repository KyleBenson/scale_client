# coding=utf-8

"""
Server to handle heartbeat messages from clients.

"""

import api_handler
import util

from messages import heartbeat_pb2


MAX_RECENT_CHANGES = 10
EVENT_RATE_REQUIRED_FIELDS = ['sensor_id', 'event_count', 'time_window']


class HeartbeatHandler(api_handler.ProtobufHandler):
    """
    Handler class for client heartbeat messages.

    """

    REQUIRE_CLIENT = True
    REQUEST_OBJ = heartbeat_pb2.HeartbeatMessage
    RESPONSE_OBJ = heartbeat_pb2.HeartbeatResponse

    def post_pb(self, client_id_str=None):
        """
	return nothing to the client when receiving a heartbeat

	heart beat
	status {
  		type: SUCCESS
	}
	data_requests {
  		sensor_id: 0
  		provide_current_data: true
	}
	latest_request_id: 0

        """
        current_time = util.system_time()

        data_request = self.response_pb.data_requests.add()
        data_request.sensor_id = 0
        data_request.provide_current_data = True
        self.response_pb.latest_request_id = 0
        self.write_response()

	print('\n\nHeartBeatHandler request');
	print(self.request_pb)
	print('\n\nHeartBeatHandler response');
	print(self.response_pb)
