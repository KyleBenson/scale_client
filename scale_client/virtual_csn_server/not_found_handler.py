# coding=utf-8

"""
404 Handler.

"""

import webapp2

class NotFoundHandler(webapp2.RequestHandler):
    """
    404 Handler.

    """

    def get(self, path):
        if path.startswith('api'):
            self.response.content_type = 'application/json'
            self.response.set_status(404)
            self.response.write('{"status": "ERR", "message": "Invalid request"}')			
        elif path.startswith('json'):
            self.response.content_type = 'application/json'
            self.response.set_status(404)
            self.response.write('{"status": "ERR", "message": "Invalid request"}')			
        else:
            self.response.content_type = 'application/json'
            self.response.set_status(404)
            self.response.write('{"status": "ERR", "message": "404 page not found"}')			

    def post(self, path):
        if path.startswith('api'):
            self.serve_404pb()
        else:
            self.get(path)

    def serve_404pb(self, status=404):
        self.response.content_type = 'application/x-protobuf'
        self.response.set_status(status)
