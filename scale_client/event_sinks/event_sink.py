from scale_client.core.application import Application
from scale_client.core.threaded_application import ThreadedApplication


class EventSink(Application):
    """EventSinks handle forwarding SensedEvents to some end-point, possibly via a particular network interface.  To
    create a new one, make use of the Application on_start() function to setup any connections or other resources
    needed."""

    def __init__(self, broker=None, **kwargs):
        super(EventSink, self).__init__(broker, **kwargs)

    def send_event(self, event):
        """
        Sends a SensedEvent object out on this sink.
        :param event: SensedEvent
        :return:
        """
        return self.send_raw(self.encode_event(event))

    def send_raw(self, encoded_event):
        """
        This function is the heart of every EventSink.  Use it to actually send raw data representing a SensedEvent
        over some connection.
        :param encoded_event: raw encoding of a SensedEvent
        :raises IOError: when there is an issue sending the event
        """
        raise NotImplementedError()

    def check_available(self, event):
        """This function is a primitive attempt at allowing EventSinks to create backpressure when too many events
        are in the system.  Expect it to disappear eventually, but for now it should return True when the EventSink is
        able to immediately send() an event over whatever connection it uses.  By default it always returns True."""
        return True

    def encode_event(self, event):
        """
        Encodes the given SensedEvent in a format that can be pushed out through the EventSink via send(event).  By
        default, it encodes the SensedEvent as a json string using event.to_json()

        :param event: SensedEvent to encode
        :return: event encoded in a format ready to be immediately pushed to send(event)
        """

        return event.to_json()

class ThreadedEventSink(EventSink, ThreadedApplication):
    """
    Use this class if you expect the EventSink to block for a long period of
    time when sinking events, connecting to a remote server, etc.
    """
    pass