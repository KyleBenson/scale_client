import logging

log = logging.getLogger(__name__)

from scale_client.event_sinks.event_sink import EventSink
from scale_client.core.application import handler

from circuits.core.timers import Timer
from circuits.core.events import Event


# TODO: this class should be rewritten using the scale client API instead of directly in circuits

class RelayScannerEventSink(EventSink):
    def __init__(self, broker=None, scan_interval=10, **kwargs):

        super(RelayScannerEventSink, self).__init__(broker=broker, **kwargs)

    # self._scan_interval = scan_interval

    def check_available(self, event):
        return self.__is_available and super(RelayScannerEventSink, self).check_available()

    def on_start(self):
        print('starting relay scanner');

    def set_event_check_timer(self, time_to_wait=7):
        try:
            self.__timer.reset(time_to_wait)
        except AttributeError:
            self.__timer = Timer(time_to_wait, RelayScannerEventSink())
            self.__timer.register(self)

    @handler("RelayScannerEventSink")
    def check_event_sent(self):
        # TODO: do this asynchronously so we don't always wait 7 seconds???
        if self.receive():
            print ('receiving something ... ')
        else:
            print ('something is wrong ... ')
            self.set_event_check_timer()

    def receive(self):
        # read message from the sigfox adapter
        ret = ''  # return message read
        while self._ser.inWaiting() > 0:
            print('in receiving method')

    def encode_event(self, event):
        print ('hi there, in encode event')
        return str(event)
