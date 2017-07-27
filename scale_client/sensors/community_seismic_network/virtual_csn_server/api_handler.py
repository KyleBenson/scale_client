# coding=utf-8

"""
Base handler for API protobuf handlers.

"""

import logging
logging.basicConfig(filename='/var/log/csn_virtual_server', level=logging.DEBUG)

import webapp2

from scale_client.sensors.community_seismic_network.virtual_csn_server import import_fixer, util

import_fixer.FixImports('protobuf')
import google.protobuf

from scale_client.sensors.community_seismic_network.virtual_csn_server.messages import common_pb2


SIGNATURE_FIELDS = ['message_id', 'date', 'signature']


# Avoid imports of util when the only thing a class needs is the exception cls.
InvalidRequest = util.InvalidRequest


# This abstract class is referenced elsewhere.
# pylint: disable=R0921
class ProtobufHandler(webapp2.RequestHandler):
    """
    Base handler for all API endpoints that read and write protocol buffers.

    Parameters
    ----------
    request : webapp2.request
        Passed to webapp2.RequestHandler.initialize method.
    response : webapp2.response
        Passed to webapp2.RequestHandler.initialize method.

    Attributes
    ----------
    REQUIRE_CLIENT : bool
        Whether or not the handler requires a client be specified in the URL.
        Additionally, if specified, requires the `request_pb` message have a
        valid signature field. Checking the signature is left to the handler.
    REQUEST_OBJ : class from messages module
        Defined by a subclass as the class for a request protocol buffer.
    RESPONSE_OBJ : class from messages module
        Defined by a subclass as the class for a response protocol buffer.
    REQUIRED_FIELDS : list of strings
        Fields that `ProtobufHandler` will guarantee the existence of before
        calling `post_pb`.
    request_pb : cls.REQUEST_OBJ
        Data submitted by the client is parsed into this parameter using the
        type specified by the subclass in the `REQUEST_OBJ` constant.
    response_pb : cls.RESPONSE_OBJ
        Data to be returned to the client is written using the type specified
        by the subclass in the `RESPONSE_OBJ` constant.

    Notes
    -----
    This class provides exception handling for platform generated exceptions
    as well as exceptions expected to be raised by App Engine's own methods.
    Because the `response_pb` object is initialized as an attribute, then no
    matter where the exception is raised, a parseable status and message can
    still be returned. Without the member object, the handler could be left in
    a state where it doesn't know what kind of response to return. An
    alternative implementation could rely on the `GenericResponse` message
    format, which is based on every response message starting with a
    `StatusMessage`.

    Error strings even from unexpected exceptions are currently returned to the
    client as part of the protocol buffer response. This is a potential
    security risk if important implementation details ever leak into the
    exception messages.

    """

    REQUIRE_CLIENT = False
    REQUEST_OBJ = None
    RESPONSE_OBJ = None
    REQUIRED_FIELDS = []

    def __init__(self, request, response):
        """Set up protocol buffer attributes and call initialize method."""
        self.initialize(request, response)
        # These variables are set with callables by subclasses.
        # pylint: disable=E1102
        self.request_pb = self.REQUEST_OBJ()
        self.response_pb = self.RESPONSE_OBJ()
        self.stats = []

    def handle_exception(self, exception, debug):
        """Make sure that all exceptions are at least logged."""
        # Determine severity level of exception. Default is warning.
        log_fn = logging.warning
        status_code = 400
        if isinstance(exception, InvalidRequest):
            status_type = common_pb2.INVALID_REQUEST
            self.stats.append('invalid_client_request')
        elif isinstance(exception, UnknownClient):
            status_type = common_pb2.UNKNOWN_CLIENT
        elif isinstance(exception, Exception):
            status_type = common_pb2.UNKNOWN_SENSOR
        elif is_deadline_error(exception):
            status_type = common_pb2.DEADLINE_EXCEEDED
            self.stats.append('deadline_error')
        elif is_datastore_error(exception):
            status_type = common_pb2.DATASTORE_ERROR
            self.stats.append('transaction_error')
        else:
            # If the exception is a HTTPException, use its error code.
            # Otherwise, use a generic 500 error code.
            if isinstance(exception, webapp2.HTTPException):
                status_code = exception.code
            else:
                status_code = 500
            # Default unknown exceptions to full stack traces.
            log_fn = logging.exception
            status_type = common_pb2.UNKNOWN_ERROR
            self.stats.append('unknown_error')

        log_fn(exception)
        try:
            self.write_response(
                exception.message, status=status_type, code=status_code)
        # If protobuf code throws an exception, let's still terminate.
        # pylint: disable=W0702
        except:
            logging.exception('Error writing protobuf exception details.')
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.set_status(status_code)
            self.response.out.write(exception.message)

    def post(self, **kwargs):
        """
        Initializes request protocol buffer and calls post_pb().

        Notes
        -----

        This method decodes incoming protocol buffers to `self.request_pb`,
        which is initialized in `__init__`. `__init__` cannot read the protocol
        buffer because any errors would then fail to call `handle_exception`.

        """

        self.stats.append('api-requests')
        try:
            self.request_pb.ParseFromString(self.request.body)
            _check_required(self.request_pb, self.REQUIRED_FIELDS)
            if self.REQUIRE_CLIENT:
                _check_required(self.request_pb.client_signature,
                                SIGNATURE_FIELDS)
            # Call the real handler.
            self.post_pb(**kwargs)
        except google.protobuf.message.DecodeError:
            raise InvalidRequest('Could not decode request.')

    def post_pb(self, **kwargs):
        """Implementation deferred to subclasses."""
        raise NotImplementedError('Implementation required.')

    def write_response(self, message=None,
                       status=common_pb2.SUCCESS, code=200):
        """
        Write self.response_pb to self.response as a protocol buffer response.

        Parameters
        ----------
        message : string, optional
            Message to include in response status. Defaults to no message.
        status : common_pb2.StatusType
            Status type enum to indicate success or failure of request.
            Defaults to success.
        code : int
            Valid HTTP status code to indicate success or failure of request.
            Defaults to 200.

        """
        #google.appengine.api.memcache.incr(self.stats, initial_value=1)
        self.response_pb.status.type = status
        if message:
            self.response_pb.status.message = message
        self.response.cache_control.no_cache = None
        self.response.content_type = 'application/x-protobuf'
        self.response.set_status(code)
        self.response.out.write(self.response_pb.SerializeToString())


def _check_required(request_pb, required_fields):
    for field in required_fields:
        if not request_pb.HasField(field):
            raise InvalidRequest('Missing required field: {}'.format(field))


def is_deadline_error(exception):
    return (
        isinstance(exception, runtime.DeadlineExceededError) or
        isinstance(exception, runtime.apiproxy_errors.DeadlineExceededError))


def is_datastore_error(exception):
    return (
        isinstance(exception, datastore_errors.TransactionFailedError) or
        isinstance(exception, datastore_errors.Timeout))


class UnknownClient(Exception):
    pass
