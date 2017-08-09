from scale_client.core.application import Application
from scale_client.sensors.virtual_sensor import VirtualSensor
from scale_client.core.sensed_event import SensedEvent
from scale_client.core.broker import Broker

# NOTE: we add sleep statements to make the progression easier to read, but we might not really want them...
import time

"""
The basic idea of this silly pub-sub demonstration is that the BombTimer will publish
a BombLit event after a few seconds, which causes the Bomb to then make a timed_call()
to publish an Explosion after a few more seconds, which will then immediately light the
Gasoline on fire (publishing a Fire event), which will then cause the FireAlarm to start
alarming every second.

Testing-wise, this demonstrates proper usage of the pub-sub system including the subscriptions parameter,
the direct publish/subscribe calls, the on_subscribe callback, the timed_call function, and the
sensor reading interval functionality as demonstrated by the FireAlarm's repeated alarming.
Consider this script as a really simple check to verify that the fundamental pub-sub system is working,
but NOT a comprehensive test of many edge cases!
"""

# TODO: test unsubscribe once implemented!

BOMB_DELAY = 3

# Rather than relying purely on print statements, we explicitly check for proper functionality,
# set these conditions, and then assert that they're successful at the end of the test.
# TODO: maybe we won't actually do this?
test_on_sub_works = False
test_on_pub_works = False
test_callback_sub_works = False

# XXX: NOTE: since we can't actually use inheritance for events in circuits, we hack our way
# around it by using functions to wrap SensedEvent constructors with default params:
def BombLit(source):
    return SensedEvent(source=source, event_type="bomb_lit", data="psssssss!!", priority=4)
def Explosion(source):
    return SensedEvent(source=source, event_type="explosion", data="BOOM!", priority=1)
def Fire(source):
    return SensedEvent(source=source, event_type="fire", data="Fire!", priority=2)
# class BombLit(SensedEvent):
#     def __init__(self, source):
#         super(BombLit, self).__init__(event_type="bomb_lit", data="psssssss!!", priority=4, source=source)
# class Explosion(SensedEvent):
#     def __init__(self, source):
#         super(Explosion, self).__init__(event_type="explosion", data="BOOM!", priority=1, source=source)
# class Fire(SensedEvent):
#     def __init__(self, source):
#         super(Fire, self).__init__(event_type="fire", data="Fire!", priority=2, source=source)


class Bomb(Application):

    def on_event(self, event, topic):
        assert event.event_type == "bomb_lit"
        print "bomb blew up!"
        time.sleep(1)
        self.publish(Explosion(self.path))


class BombTimer(Application):

    def on_start(self):
        self.timed_call(BOMB_DELAY, function=self.__class__.light_bomb)
        print "BombTimer fuse started..."
        super(BombTimer, self).on_start()

    def light_bomb(self):
        print "BombTimer: lighting a bomb..."
        time.sleep(1)
        self.publish(BombLit(self.path))


class DudBomb(Bomb):
    """
    This class currently verifies that it won't get any events since it hasn't subscribed...
    """

    def on_event(self, event, topic):
        # TODO: check for explosion and blow up again?  would go with
        # gasoline only blowing up once.  BUT, we don't have unsubscribe yet...
        assert False, "DudBomb hasn't subscribed to ANYTHING!"


class Gasoline(Application):
    """The gasoline starts a fire after the explosion"""

    def on_event(self, event, topic):
        # TODO: don't start a fire the second time
        assert event.event_type == 'explosion'
        time.sleep(1)
        self.publish(Fire(self.path))

    def on_publish(self, event, topic):
        print "the gasoline caught fire!"
        global test_on_pub_works
        test_on_pub_works = True


class FireAlarm(VirtualSensor):

    DEFAULT_PRIORITY = 1

    def __init__(self, broker, **kwargs):
        super(FireAlarm, self).__init__(broker, event_type="fire_alarm", sample_interval=1, **kwargs)
        self._fire_detected = False
        self.subscribe('fire', self.__class__.on_fire)

        # we'll quit the test after issuing self.max_alarms
        self.nalarms = 0
        self.max_alarms = 5
        self.subscribe("fire_alarm", self.__class__.on_alarm)

    def on_subscribe(self, topic):
        print 'FireAlarm armed and ready!'
        global test_on_sub_works
        test_on_sub_works = True

    def on_fire(self, fire_event):
        """Record that we detected the fire and then we'll start publishing alarms."""
        global test_callback_sub_works
        test_callback_sub_works = True
        assert fire_event.event_type == 'fire', "on_fire got non-fire event!"
        print "FireAlarm: beep beep! FIRE!"
        self._fire_detected = True

    def on_alarm(self, event):
        """Monitor our own alarms and quit the test after several of them"""
        self.nalarms += 1
        assert event.event_type == "fire_alarm"
        if self.nalarms > self.max_alarms:
            print "stopping after %d alarms" % self.max_alarms
            self._broker.stop()
            self.stop()

    def read_raw(self):
        return "beep! beep! fire!"

    def policy_check(self, event):
        """
        Only publish an alarm event after we've detected the first fire!
        :param event:
        :return:
        """
        return self._fire_detected


class Logger(Application):

    def on_event(self, event, topic):
        print "log event:", event


def main():
    broker = Broker()

    # In order of actions that affect the flow:
    bomb_timer = BombTimer(broker)
    bomb = Bomb(broker, subscriptions=("bomb_lit",))
    # bomb.subscribe("bomb_lit")
    gas = Gasoline(broker)
    gas.subscribe("explosion")
    alarm = FireAlarm(broker)
    # this one doesn't blow up!
    dud_bomb = DudBomb(broker)

    logger = Logger(broker, subscriptions=('*',))

    # Run until the alarm calls it quits
    broker.run()

    assert test_on_pub_works
    assert test_callback_sub_works
    assert test_on_sub_works

    print "TEST PASSED SUCCESSFULLY!"

if __name__ == "__main__":
    main()