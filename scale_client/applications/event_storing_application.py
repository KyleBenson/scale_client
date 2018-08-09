from scale_client.core.application import Application

import logging
log = logging.getLogger(__name__)


class EventStoringApplication(Application):
    """
    This Application stores all of its received events that it subscribed to in memory. Mainly intended for testing.
    WARNING: if you let this Application run for a very long time, you'll end up with a huge list of sunk events that may
    cause memory problems
    """

    def __init__(self, broker, remote_only=False, **kwargs):
        super(EventStoringApplication, self).__init__(broker, **kwargs)
        self.__events = []

        self._remote_only = remote_only

    def on_event(self, event, topic):
        """
        :param event:
        :type event: scale_client.core.sensed_event.SensedEvent
        :param topic:
        :return:
        """

        if not self._remote_only or not event.is_local:
            self.__events.append(event)
        super(EventStoringApplication, self).on_event(event, topic)

    @property
    def events(self):
        """
        :rtype: list[SensedEvent]
        """
        return self.__events
