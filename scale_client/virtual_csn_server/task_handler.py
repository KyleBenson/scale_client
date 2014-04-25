"""
Define the base handler for tasks.

"""

import logging

import webapp2

import util


class TaskHandler(webapp2.RequestHandler):

    def handle_exception(self, exception, debug):
        """Make sure that all exceptions are at least logged."""
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Error')
        if isinstance(exception, util.InvalidRequest):
            # Do not retry this task; it is malformed.
            self.response.set_status(200)
            logging.exception('Could not complete task; malformed.')
            return

        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)
            logging.exception('Unknown error.')

    def check_required(self, required):
        required_params = {}
        for field in required:
            required_params[field] = self.request.get(field)
            if not required_params[field]:
                raise util.InvalidRequest(
                    'Parameter {} is required.'.format(field))
        return required_params
