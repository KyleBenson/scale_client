#!/usr/bin/python
# coding=utf-8

"""
Routing module.

"""

import webapp2
import webapp2_extras.routes
import event_server

#XXX
print "Loading HTTP server module"

APP_CONFIG = {
    'webapp2_extras.sessions': {
        'cookie_name': '_saf',
        'secret_key': 'test',
    },
}

base_app = webapp2.WSGIApplication([
    # API routes.
    webapp2_extras.routes.PathPrefixRoute(r'/api/v1/csn', [
        # Event Server routes.
        webapp2.Route(r'/event/<client_id_str:\d+>',
                      handler='event_server.EventHandler',
                      name='event'),
        # Heartbeat Server routes.
        webapp2.Route(r'/heartbeat/<client_id_str:\d+>',
                      handler='heartbeat_server.HeartbeatHandler',
                      name='heartbeat'),
        # Client Server routes.
        webapp2_extras.routes.PathPrefixRoute(r'/client', [
            webapp2.Route(r'/create',
                          handler='client_server.CreateHandler',
                          name='client-create'),
            webapp2.Route(r'/update/<client_id_str:\d+>',
                          handler='client_server.UpdateHandler',
                          name='client-update'),
            webapp2.Route(r'/metadata/<client_id_str:\d+>',
                          handler='client_server.MetadataHandler',
                          name='client-metadata'),
        ]),
    ]),

   # Task routes.
    webapp2_extras.routes.PathPrefixRoute('/task/<namespace:[^/]+>', [
        # Active Clients Server routes.
        webapp2_extras.routes.PathPrefixRoute(r'/active', [
            webapp2.Route(r'/set/<client_id_str:\d+>',
                          handler='active_clients_server.SetActiveHandler',
                          name='active-set'),
            webapp2.Route(r'/change/<geostr>/<active_str>',
                          handler='active_clients_server.ChangeHandler',
                          name='active-change'),
            webapp2.Route(r'/geocell/<geostr>/<active_str>',
                          handler='active_clients_server.GeocellHandler',
                          name='active-geocell'),
            webapp2.Route(r'/backup/<geostr>/<action>',
                          handler='active_clients_server.BackupHandler',
                          name='active-backup'),
        ]),
    ]),
    # Default route.
    webapp2.Route(r'/<path:.*>',
                  handler='not_found_handler.NotFoundHandler',
                  name='not-found'),
], config=APP_CONFIG, debug=True)

def main():
    from paste import httpserver

    #XXX
    print "Starting local HTTP server"
    httpserver.serve(base_app, host='127.0.0.1', port='80')

if __name__ == '__main__':
    main()

